#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import logging
import traceback
from datetime import datetime, timedelta
from typing import Optional

from ...database.session import get_db
from ...database.models import Account
from .token_refresh import refresh_account_token

logger = logging.getLogger(__name__)

class TokenRefreshWorker:
    """
    Token 自动刷新后台工作线程
    定期检查数据库中即将过期或已失效的账号并尝试刷新
    """
    def __init__(self, interval_seconds: int = 3600):
        self.interval = interval_seconds
        self.running = False
        self._task: Optional[asyncio.Task] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def set_loop(self, loop: asyncio.AbstractEventLoop):
        """设置事件循环"""
        self._loop = loop

    async def start(self):
        """启动工作线程"""
        if self.running:
            return
        self.running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info(f"Token 自动刷新工作线程已启动，扫描间隔: {self.interval}s")

    def stop(self):
        """停止工作线程"""
        self.running = False
        if self._task:
            self._task.cancel()
        logger.info("Token 自动刷新工作线程已停止")

    async def _run_loop(self):
        """主循环"""
        # 启动后先延迟一小会儿，避开系统启动高峰
        await asyncio.sleep(60)
        
        while self.running:
            try:
                await self.perform_refresh_scan()
            except Exception as e:
                logger.error(f"TokenRefreshWorker 运行异常: {e}\n{traceback.format_exc()}")
            
            # 等待下一个周期
            if self.running:
                await asyncio.sleep(self.interval)

    async def perform_refresh_scan(self):
        """执行一次刷新扫描"""
        logger.info("开始执行定期 Token 刷新扫描...")
        
        # 策略：
        # 1. 状态为 expired 或 failed 的账号
        # 2. 距离过期时间少于 12 小时的账号 (OpenAI Token 默认 24h)
        # 3. 排除 status 为 banned 的账号
        
        now = datetime.utcnow()
        expiry_threshold = now + timedelta(hours=12)
        
        with get_db() as db:
            # 查找需要刷新的账号 ID
            # 注意：不要在 session 中直接迭代处理，避免长事务。先查出 ID 列表。
            query = db.query(Account.id, Account.email).filter(
                (Account.status.in_(['expired', 'failed'])) |
                (Account.expires_at < expiry_threshold)
                | (Account.access_token == None) # 补全缺失 token 的账号
            ).filter(Account.status != 'banned')
            
            accounts_to_refresh = query.all()
            
            if not accounts_to_refresh:
                logger.info("没有发现需要刷新的账号")
                return

            logger.info(f"发现 {len(accounts_to_refresh)} 个账号需要刷新")
            
            for acc_id, email in accounts_to_refresh:
                if not self.running:
                    break
                
                logger.info(f"正在后台自动续期账号: {email} (ID: {acc_id})")
                
                try:
                    # 使用 asyncio.to_thread 运行同步的刷新函数，避免阻塞事件循环
                    # auto_sync=True 会确保如果账号已上传过 CPA，则刷新后自动同步
                    result = await asyncio.to_thread(refresh_account_token, acc_id, auto_sync=True)
                    
                    if result.success:
                        logger.info(f"账号 {email} 自动续期并同步成功")
                    else:
                        logger.warning(f"账号 {email} 自动续期失败: {result.error_message}")
                except Exception as e:
                    logger.error(f"处理账号 {email} 时发生异常: {e}")
                
                # 账号之间稍微停顿下，防止并发请求过快触发 OpenAI 频率限制
                await asyncio.sleep(10)

# 全局单例
token_refresh_worker = TokenRefreshWorker(interval_seconds=3600)
