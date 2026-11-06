---
sop_id: "SOP-AUTH-001"
title: "Active Directory Domain Account Locked Out"
category: "Authentication"
symptoms:
  - "tài khoản bị khóa"
  - "the referenced account is currently locked out"
  - "account locked out"
  - "khóa tài khoản domain"
  - "nhập sai mật khẩu nhiều lần bị khóa"
prerequisites:
  device_type: ["Windows", "macOS"]
steps:
  - step_id: 1
    action: "Kiểm tra trạng thái khóa tự động và thời gian chờ unlock tự động (thường 15 phút)."
    instruction_spoken: "Tài khoản của bạn tạm thời bị khóa do nhập sai mật khẩu nhiều lần. Bạn có muốn đợi 15 phút để tài khoản tự mở, hay cần IT mở khóa ngay bây giờ?"
    expected_confirmation:
      - "cần mở khóa ngay"
      - "mở giúp tôi luôn"
      - "mở ngay"
      - "tôi đợi được"
    fallback_instruction: "Chính sách bảo mật công ty sẽ tự động giải phóng tài khoản sau 15 phút nếu không tiếp tục có yêu cầu đăng nhập sai."
    shortcut: "Wait 15 mins OR AD Self-Service Portal"
  - step_id: 2
    action: "Xác minh thông tin định danh nhân viên và email công ty."
    instruction_spoken: "Để mở khóa ngay, bạn đọc giúp mình Mã số nhân viên hoặc họ tên và địa chỉ email công ty của bạn nhé."
    expected_confirmation:
      - "đã đọc xong"
      - "mã nhân viên là"
      - "email của tôi là"
      - "xong rồi"
    fallback_instruction: "Bạn có thể gửi tin nhắn qua ứng dụng chat nội bộ Teams/Slack cho kênh IT Helpdesk kèm ảnh thẻ nhân viên nếu cần."
    shortcut: "Verify Employee ID & Email"
  - step_id: 3
    action: "Xóa thông tin đăng nhập cũ được lưu trong Windows Credential Manager."
    instruction_spoken: "Sau khi mình mở khóa, bạn mở Credential Manager trên máy, xóa các mật khẩu Outlook hoặc Teams cũ đã lưu để tránh bị khóa lại nhé."
    expected_confirmation:
      - "đã xóa credential cũ"
      - "đăng nhập lại được rồi"
      - "vào được windows rồi"
      - "thành công rồi"
    fallback_instruction: "Gõ Credential Manager vào thanh tìm kiếm Start, chọn Windows Credentials và xóa các mục có tên MicrosoftOffice hoặc Teams."
    shortcut: "Control Panel -> Credential Manager -> Windows Credentials -> Remove Old"
---
# Hướng Dẫn Xử Lý Khóa Tài Khoản Active Directory (Account Lockout)
