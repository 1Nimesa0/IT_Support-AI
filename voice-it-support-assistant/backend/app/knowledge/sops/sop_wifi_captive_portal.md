---
sop_id: "SOP-WIFI-005"
title: "Guest or Corporate Captive Portal Login Page Not Loading"
category: "Network"
symptoms:
  - "không hiện trang đăng nhập wifi"
  - "captive portal not opening"
  - "wifi khách không load trang web login"
  - "không hiện form đăng nhập wifi"
  - "chưa xác thực mạng khách"
prerequisites:
  device_type: ["Windows", "macOS", "Mobile"]
steps:
  - step_id: 1
    action: "Buộc trình duyệt mở trang HTTP không bảo mật để kích hoạt chuyển hướng Captive Portal."
    instruction_spoken: "Bạn mở trình duyệt web lên và gõ địa chỉ: neverssl chấm com hoặc một chấm một chấm một chấm một để trang đăng nhập hiện lên nhé."
    expected_confirmation:
      - "đã hiện trang đăng nhập rồi"
      - "thấy form login rồi"
      - "hiện ra trang đăng nhập"
      - "xong rồi"
    fallback_instruction: "Nếu trình duyệt báo chặn HSTS, hãy mở tab ẩn danh Incognito rồi gõ địa chỉ http://captive.apple.com hoặc http://detectportal.firefox.com."
    shortcut: "Browser -> http://neverssl.com"
  - step_id: 2
    action: "Tạm thời tắt phần mềm VPN hoặc DNS bên thứ ba (như Cloudflare WARP hay AdGuard)."
    instruction_spoken: "Bạn kiểm tra xem có đang bật VPN hoặc phần mềm chặn quảng cáo không nhé, tạm thời tắt đi để nhận trang chuyển hướng."
    expected_confirmation:
      - "đã tắt vpn rồi"
      - "tắt chặn quảng cáo rồi"
      - "trang login đã hiện"
      - "xong rồi"
    fallback_instruction: "Bạn có thể vào khay hệ thống cạnh đồng hồ để tìm icon VPN và chọn Disconnect."
    shortcut: "System Tray -> Disconnect VPN / Custom DNS"
  - step_id: 3
    action: "Đồng ý điều khoản hoặc nhập số điện thoại / mã khách mời."
    instruction_spoken: "Bây giờ bạn tích chọn Đồng ý với điều khoản dịch vụ và nhập mã OTP hoặc số điện thoại theo yêu cầu trên màn hình nhé."
    expected_confirmation:
      - "đã đăng nhập thành công"
      - "vào mạng được rồi"
      - "đã truy cập internet"
    fallback_instruction: "Nếu mã OTP không về, bạn hãy nhấn Gửi lại mã sau 60 giây hoặc nhờ tiếp tân hỗ trợ cấp voucher Wi-Fi mới."
    shortcut: "Accept Terms -> Connect"
---
# Hướng Dẫn Kích Hoạt Trang Đăng Nhập Wi-Fi Khách (Captive Portal)
