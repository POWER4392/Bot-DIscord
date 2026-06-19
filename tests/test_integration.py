import unittest
import asyncio
import json
import os
import sys
from unittest.mock import MagicMock
from aiohttp import web
import aiohttp

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.api_server import create_handle_api, cors_middleware, rate_limit_middleware, handle_health, _rate_limit_store
from core.shared import API_SECRET
from core.database import cursor, conn, db_lock

class TestBotIntegration(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # Reset rate limit store
        _rate_limit_store.clear()

        # Mock discord bot
        self.bot = MagicMock()
        self.bot.user = "TestBot#1337"
        self.bot.guilds = []
        self.bot.latency = 0.045
        self.bot.cogs = {"AIChatbot": MagicMock(chat_sessions={}, model_name="gemini-1.5-flash")}
        self.bot.is_ready = MagicMock(return_value=True)
        
        # Setup clean test tables
        with db_lock:
            cursor.execute("DELETE FROM reaction_panels")
            cursor.execute("DELETE FROM ai_token_usage")
            conn.commit()

        # Initialize API Web App
        self.app = web.Application(middlewares=[cors_middleware, rate_limit_middleware])
        self.app["bot"] = self.bot
        self.app.router.add_post("/api", create_handle_api(self.bot))
        self.app.router.add_get("/health", handle_health)
        
        # Start server on dynamic port
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, "127.0.0.1", 0)
        await self.site.start()
        
        self.port = self.runner.addresses[0][1]
        self.url = f"http://127.0.0.1:{self.port}"

    async def asyncTearDown(self):
        await self.runner.cleanup()

    async def test_health_check(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.url}/health") as resp:
                self.assertEqual(resp.status, 200)
                data = await resp.json()
                self.assertEqual(data["status"], "ok")
                self.assertTrue(data["bot_online"])
                self.assertEqual(data["bot_user"], "TestBot#1337")
                self.assertIn("database", data)

    async def test_unauthorized_access(self):
        async with aiohttp.ClientSession() as session:
            payload = {"action": "DELETE_REACTION_ROLE", "payload": {"message_id": "123"}}
            headers = {"X-API-Key": "incorrect_secret_key", "Content-Type": "application/json"}
            async with session.post(f"{self.url}/api", json=payload, headers=headers) as resp:
                self.assertEqual(resp.status, 401)
                data = await resp.json()
                self.assertFalse(data["ok"])
                self.assertEqual(data["error"], "Unauthorized")

    async def test_forbidden_access(self):
        from core.shared import config
        config["api_secrets"] = ["valid_non_owner_key"]
        async with aiohttp.ClientSession() as session:
            payload = {"action": "DELETE_REACTION_ROLE", "payload": {"message_id": "123"}}
            headers = {"X-API-Key": "valid_non_owner_key", "Content-Type": "application/json"}
            async with session.post(f"{self.url}/api", json=payload, headers=headers) as resp:
                self.assertEqual(resp.status, 403)
                data = await resp.json()
                self.assertFalse(data["ok"])
                self.assertEqual(data["error"], "Unauthorized")

    async def test_invalid_action(self):
        async with aiohttp.ClientSession() as session:
            payload = {"action": "INVALID_ACTION_123"}
            headers = {"X-API-Key": API_SECRET, "Content-Type": "application/json"}
            async with session.post(f"{self.url}/api", json=payload, headers=headers) as resp:
                self.assertEqual(resp.status, 400)
                data = await resp.json()
                self.assertFalse(data["ok"])
                self.assertEqual(data["error"], "Unknown action")

    async def test_get_and_delete_reaction_roles(self):
        # Insert a mock reaction panel config
        with db_lock:
            cursor.execute(
                "INSERT INTO reaction_panels (message_id, guild_id, roles_json) VALUES (?, ?, ?)",
                ("11223344", "9999999", json.dumps([{"name": "Verified", "desc": "Access role"}]))
            )
            conn.commit()

        async with aiohttp.ClientSession() as session:
            headers = {"X-API-Key": API_SECRET, "Content-Type": "application/json"}
            
            # 1. Fetch active reaction panels
            async with session.post(f"{self.url}/api", json={"action": "GET_REACTION_ROLES"}, headers=headers) as resp:
                self.assertEqual(resp.status, 200)
                data = await resp.json()
                self.assertTrue(data["ok"])
                self.assertEqual(len(data["panels"]), 1)
                self.assertEqual(data["panels"][0]["message_id"], "11223344")
                self.assertEqual(data["panels"][0]["roles"][0]["name"], "Verified")

            # 2. Delete the reaction panel
            payload = {"action": "DELETE_REACTION_ROLE", "payload": {"message_id": "11223344"}}
            async with session.post(f"{self.url}/api", json=payload, headers=headers) as resp:
                self.assertEqual(resp.status, 200)
                data = await resp.json()
                self.assertTrue(data["ok"])

            # 3. Verify deletion
            async with session.post(f"{self.url}/api", json={"action": "GET_REACTION_ROLES"}, headers=headers) as resp:
                data = await resp.json()
                self.assertEqual(len(data["panels"]), 0)

    async def test_get_bot_metrics_and_token_history(self):
        # Insert mock token usage records
        with db_lock:
            cursor.execute(
                "INSERT INTO ai_token_usage (guild_id, user_id, prompt_tokens, completion_tokens, total_tokens, timestamp, latency_ms) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                ("9999999", "55555", 100, 50, 150, 1625000000.0, 320)
            )
            conn.commit()

        async with aiohttp.ClientSession() as session:
            headers = {"X-API-Key": API_SECRET, "Content-Type": "application/json"}
            async with session.post(f"{self.url}/api", json={"action": "GET_BOT_METRICS"}, headers=headers) as resp:
                self.assertEqual(resp.status, 200)
                data = await resp.json()
                self.assertTrue(data["ok"])
                self.assertEqual(data["ai_total_prompt_tokens"], 100)
                self.assertEqual(data["ai_total_completion_tokens"], 50)
                self.assertEqual(data["ai_total_tokens"], 150)
                self.assertEqual(len(data["token_history"]), 1)
                self.assertEqual(data["token_history"][0]["latency_ms"], 320)

    async def test_rate_limiting(self):
        async with aiohttp.ClientSession() as session:
            headers = {"X-API-Key": API_SECRET, "Content-Type": "application/json"}
            payload = {"action": "STATUS"}
            
            # Send 30 requests (allowed)
            for _ in range(30):
                async with session.post(f"{self.url}/api", json=payload, headers=headers) as resp:
                    self.assertEqual(resp.status, 200)
            
            # 31st request should be rate-limited (429)
            async with session.post(f"{self.url}/api", json=payload, headers=headers) as resp:
                self.assertEqual(resp.status, 429)
                data = await resp.json()
                self.assertFalse(data["ok"])
                self.assertIn("Quá nhiều yêu cầu", data["error"])

if __name__ == "__main__":
    unittest.main()
