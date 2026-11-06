---
sop_id: "SOP-WIFI-002"
title: "Connecting to Hidden Enterprise Wi-Fi SSID"
category: "Network"
symptoms:
  - "không tìm thấy tên wifi công ty"
  - "wifi bị ẩn"
  - "hidden network"
  - "không thấy mạng nội bộ"
  - "mạng wifi không hiện trong danh sách"
prerequisites:
  device_type: ["Windows", "macOS"]
steps:
  - step_id: 1
    action: "Mở cài đặt mạng và chọn kết nối mạng ẩn."
    instruction_spoken: "Bạn bấm vào biểu tượng mạng ở góc phải thanh Taskbar, cuộn xuống dưới cùng và chọn Mạng ẩn (Hidden Network) rồi bấm Connect nhé."
    expected_confirmation:
      - "đã chọn mạng ẩn rồi"
      - "thấy ô nhập tên rồi"
      - "xong rồi"
      - "đã bấm connect"
    fallback_instruction: "Bạn có thể mở Settings bằng phím Windows cộng I, vào Network & Internet, chọn Wi-Fi rồi chọn Manage known networks và bấm Add network."
    shortcut: "Win + I -> Network & Internet -> Wi-Fi -> Add network"
  - step_id: 2
    action: "Nhập đúng tên SSID và loại bảo mật."
    instruction_spoken: "Bạn nhập tên mạng là Corp-Internal, chọn loại bảo mật là WPA2-Enterprise hoặc WPA3-Personal theo hướng dẫn rồi nhấn Next nhé."
    expected_confirmation:
      - "đã nhập corp internal rồi"
      - "đã gõ tên mạng"
      - "xong rồi"
    fallback_instruction: "Lưu ý tên SSID phân biệt chữ hoa chữ thường, bạn chú ý viết hoa chữ C và chữ I giúp mình."
    shortcut: "SSID: Corp-Internal"
  - step_id: 3
    action: "Nhập thông tin xác thực tài khoản công ty."
    instruction_spoken: "Bây giờ bạn nhập tên đăng nhập và mật khẩu tài khoản văn phòng của bạn rồi nhấn Connect để hoàn tất kết nối."
    expected_confirmation:
      - "đã kết nối thành công"
      - "vào được rồi"
      - "báo connected rồi"
    fallback_instruction: "Nếu hệ thống báo chứng chỉ không xác định, bạn nhấn Connect anyway để tiếp tục chấp nhận chứng chỉ nội bộ."
    shortcut: "Nhập User domain & Password"
---
# Hướng Dẫn Kết Nối Mạng Wi-Fi Doanh Nghiệp Bị Ẩn SSID

## Mô tả
Quy trình giúp nhân viên kết nối thiết bị cá nhân hoặc máy tính công ty vào mạng không dây bảo mật nội bộ ẩn SSID (Hidden Network).
