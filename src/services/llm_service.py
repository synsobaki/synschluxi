from __future__ import annotations

import base64
import json
import os
import re
import ssl
import uuid
from urllib import parse, request


class LLMService:
    def __init__(self) -> None:
        self.provider = (os.getenv("LLM_PROVIDER") or "openai").strip().lower()
        self.api_key = (os.getenv("LLM_API_KEY") or "").strip()
        self.model = (os.getenv("LLM_MODEL") or "").strip()
        default_base = "https://gigachat.devices.sberbank.ru/api/v1" if self.provider == "gigachat" else "https://api.openai.com/v1"
        self.base_url = (os.getenv("LLM_BASE_URL") or default_base).rstrip("/")
        self.timeout_s = self._safe_int(os.getenv("LLM_TIMEOUT_S"), 35)
        self.insecure_ssl = (os.getenv("LLM_INSECURE_SSL") or "0").strip() in {"1", "true", "yes"}

        # GigaChat settings
        self.gigachat_auth_key = (os.getenv("GIGACHAT_AUTH_KEY") or "").strip()
        self.gigachat_scope = (os.getenv("GIGACHAT_SCOPE") or "GIGACHAT_API_PERS").strip()
        self.gigachat_oauth_url = (os.getenv("GIGACHAT_OAUTH_URL") or "https://ngw.devices.sberbank.ru:9443/api/v2/oauth").strip()

    @staticmethod
    def _safe_int(value: str | None, default: int) -> int:
        try:
            if value is None:
                return default
            return int(str(value).strip())
        except Exception:
            return default

    @property
    def enabled(self) -> bool:
        if self.provider == "gigachat":
            return bool(self.gigachat_auth_key and self.model)
        return bool(self.api_key and self.model)

    def _post_json_openai(self, path: str, payload: dict) -> dict | None:
        if not self.enabled:
            return None
        url = f"{self.base_url}{path}"
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = request.Request(url=url, data=data, method="POST")
        req.add_header("Authorization", f"Bearer {self.api_key}")
        req.add_header("Content-Type", "application/json")
        try:
            with self._urlopen(req) as response:
                body = response.read().decode("utf-8", errors="replace")
                parsed = json.loads(body)
                if isinstance(parsed, dict):
                    return parsed
        except Exception:
            return None
        return None

    def _gigachat_access_token(self) -> str | None:
        if not self.gigachat_auth_key:
            return None
        form = parse.urlencode({"scope": self.gigachat_scope}).encode("utf-8")
        req = request.Request(self.gigachat_oauth_url, data=form, method="POST")
        req.add_header("Content-Type", "application/x-www-form-urlencoded")
        req.add_header("Accept", "application/json")
        req.add_header("RqUID", str(uuid.uuid4()))

        # Usually docs expect Authorization: Basic base64(client_id:client_secret)
        # but we keep compatibility with already prepared key in env.
        if self.gigachat_auth_key.lower().startswith("basic "):
            auth_header = self.gigachat_auth_key
        elif ":" in self.gigachat_auth_key:
            raw = self.gigachat_auth_key.encode("utf-8")
            auth_header = "Basic " + base64.b64encode(raw).decode("ascii")
        else:
            auth_header = f"Basic {self.gigachat_auth_key}"
        req.add_header("Authorization", auth_header)

        try:
            with self._urlopen(req) as response:
                body = response.read().decode("utf-8", errors="replace")
                parsed = json.loads(body)
                token = parsed.get("access_token") if isinstance(parsed, dict) else None
                return str(token) if token else None
        except Exception:
            return None

    def _post_json_gigachat(self, payload: dict) -> dict | None:
        token = self._gigachat_access_token()
        if not token:
            return None
        url = f"{self.base_url}/chat/completions"
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = request.Request(url=url, data=data, method="POST")
        req.add_header("Authorization", f"Bearer {token}")
        req.add_header("Content-Type", "application/json")
        req.add_header("Accept", "application/json")
        try:
            with self._urlopen(req) as response:
                body = response.read().decode("utf-8", errors="replace")
                parsed = json.loads(body)
                return parsed if isinstance(parsed, dict) else None
        except Exception:
            return None

    def _urlopen(self, req: request.Request):
        if self.insecure_ssl:
            return request.urlopen(req, timeout=self.timeout_s, context=ssl._create_unverified_context())
        return request.urlopen(req, timeout=self.timeout_s)

    def _extract_json_object(self, content: str) -> dict | None:
        raw = content.strip()
        if raw.startswith("```"):
            raw = re.sub(r"^```(?:json)?\s*", "", raw)
            raw = re.sub(r"\s*```$", "", raw)
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, dict) else None
        except Exception:
            pass
        match = re.search(r"\{[\s\S]*\}", raw)
        if not match:
            return None
        try:
            parsed = json.loads(match.group(0))
            return parsed if isinstance(parsed, dict) else None
        except Exception:
            return None

    def _extract_message_content(self, data: dict) -> str | None:
        try:
            content = data["choices"][0]["message"]["content"]
        except Exception:
            return None
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            return "".join(str(c.get("text", "")) if isinstance(c, dict) else str(c) for c in content)
        if isinstance(content, dict):
            return str(content.get("text", ""))
        return str(content)

    def _chat_json(self, system_prompt: str, user_prompt: str) -> dict | None:
        payload: dict = {
            "model": self.model,
            "temperature": 0.4,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        if self.provider == "gigachat":
            data = self._post_json_gigachat(payload)
        else:
            payload["response_format"] = {"type": "json_object"}
            data = self._post_json_openai("/chat/completions", payload)
            if not data:
                payload.pop("response_format", None)
                data = self._post_json_openai("/chat/completions", payload)
        if not data:
            return None
        try:
            content = self._extract_message_content(data)
            if not content:
                return None
            return self._extract_json_object(content)
        except Exception:
            return None

    def generate_sections(self, topic: str, mode_label: str, plan: list[str], context: str) -> list[dict[str, str]] | None:
        system_prompt = (
            "Ты автор учебных конспектов. Пиши как репетитор: по делу, понятно, без мета-комментариев. "
            "Верни только JSON объект формата {\"sections\":[{\"title\":str,\"body\":str}]}. "
            "В body используй абзацы и маркированные списки. Никаких фраз про промпты, RAG, источники."
        )
        user_prompt = (
            f"Тема: {topic}\n"
            f"Формат: {mode_label}\n"
            f"План: {json.dumps(plan, ensure_ascii=False)}\n"
            f"Контекст: {context[:3000]}\n\n"
            "Сделай содержательный конспект по каждому пункту плана."
        )
        obj = self._chat_json(system_prompt, user_prompt)
        if not obj:
            return None
        raw_sections = obj.get("sections")
        if not isinstance(raw_sections, list) or not raw_sections:
            return None
        sections: list[dict[str, str]] = []
        for i, sec in enumerate(raw_sections, start=1):
            if not isinstance(sec, dict):
                continue
            title = str(sec.get("title", "")).strip() or (plan[i - 1] if i - 1 < len(plan) else f"Раздел {i}")
            body = str(sec.get("body", "")).strip()
            if not body:
                continue
            sections.append({"id": str(i), "title": title, "body": body})
        return sections or None

    def generate_test(self, sections: list[dict[str, str]]) -> list[dict[str, object]] | None:
        system_prompt = (
            "Ты создаёшь проверочные тесты по конспекту. Верни JSON объект формата "
            "{\"questions\":[{\"question\":str,\"options\":[str,str,str,str],\"correct\":0..3,\"explanation\":str,\"section_title\":str}]}. "
            "Вопросы должны проверять понимание разделов, без шуточных/бессмысленных вариантов."
        )
        compact_sections = [{"title": s.get("title", ""), "body": str(s.get("body", ""))[:600]} for s in sections]
        user_prompt = "Сформируй по 1 вопросу на каждый раздел. " f"Разделы: {json.dumps(compact_sections, ensure_ascii=False)}"
        obj = self._chat_json(system_prompt, user_prompt)
        if not obj:
            return None
        raw = obj.get("questions")
        if not isinstance(raw, list) or not raw:
            return None
        questions: list[dict[str, object]] = []
        for i, q in enumerate(raw, start=1):
            if not isinstance(q, dict):
                continue
            options = q.get("options")
            if not isinstance(options, list) or len(options) != 4:
                continue
            try:
                correct = int(q.get("correct", 0))
            except Exception:
                continue
            if correct < 0 or correct > 3:
                continue
            section_title = str(q.get("section_title", "")).strip() or str(sections[min(i - 1, len(sections) - 1)].get("title", f"Раздел {i}"))
            questions.append(
                {
                    "id": i,
                    "question": str(q.get("question", "")).strip(),
                    "options": [str(o).strip() for o in options],
                    "correct": correct,
                    "explanation": str(q.get("explanation", "")).strip(),
                    "section_title": section_title,
                    "section_id": str(i),
                }
            )
        return questions or None
