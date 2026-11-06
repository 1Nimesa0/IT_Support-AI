"""
Tests for ASR Service and IT Domain Text Normalization (TN).
Verifies phonetic repairs, spoken number conversion, and domain biasing.
"""

import pytest
from app.modules.asr_service import ASRService


def test_phonetic_repair_ipconfig():
    raw_texts = [
        "bạn gõ lệnh ai-pi-con-phích nhé",
        "hãy mở cmd và nhập ai pi con phích",
        "tôi đã thử íp con phích rồi",
    ]
    for text in raw_texts:
        normalized = ASRService.apply_text_normalization(text)
        assert "ipconfig" in normalized, f"Expected 'ipconfig' in '{normalized}'"


def test_phonetic_repair_acronyms():
    test_cases = [
        ("máy chủ đi-hắt-xe-bê không cấp địa chỉ", "DHCP"),
        ("kết nối qua vi-pi-en bị lỗi bắt tay", "VPN"),
        ("kiểm tra lại máy chủ đê nờ ét", "DNS"),
        ("nhập tên mạng ét ét ai đi Corp-Internal", "SSID"),
        ("mở cửa sổ cờ mờ đê lên", "cmd"),
        ("nhập mã ô-tê-pê sáu số", "OTP"),
        ("xác thực bằng mờ ép a", "MFA"),
    ]
    for raw, expected in test_cases:
        normalized = ASRService.apply_text_normalization(raw)
        assert expected in normalized, f"Expected '{expected}' in '{normalized}'"


def test_spoken_ip_normalization():
    test_cases = [
        ("bạn gõ ping tám chấm tám chấm tám chấm tám giúp mình", "8.8.8.8"),
        ("thử truy cập một chấm một chấm một chấm một xem", "1.1.1.1"),
        ("ping 8 chấm 8 chấm 8 chấm 8 xem có reply không", "8.8.8.8"),
    ]
    for raw, expected in test_cases:
        normalized = ASRService.apply_text_normalization(raw)
        assert expected in normalized, f"Expected '{expected}' in '{normalized}'"


def test_command_syntax_cleaning():
    raw = "gõ ipconfig / flushdns rồi ipconfig / renew"
    normalized = ASRService.apply_text_normalization(raw)
    assert "/flushdns" in normalized
    assert "/renew" in normalized


def test_domain_biasing_prompt():
    prompt = ASRService.DOMAIN_PROMPT
    assert "ipconfig" in prompt.lower()
    assert "8.8.8.8" in prompt
    assert "dhcp" in prompt.lower()
    assert "vpn" in prompt.lower()
