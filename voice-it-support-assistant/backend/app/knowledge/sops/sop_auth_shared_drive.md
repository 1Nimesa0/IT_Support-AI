---
sop_id: "SOP-AUTH-004"
title: "Shared Network Drive Access Denied or Credential Mismatch"
category: "Authentication"
symptoms:
  - "không vào được ổ đĩa chung"
  - "access denied shared drive"
  - "ổ đĩa mạng báo đỏ gạch chéo"
  - "network path not found"
  - "không có quyền truy cập thư mục chung"
prerequisites:
  device_type: ["Windows", "macOS"]
steps:
  - step_id: 1
    action: "Kiểm tra kết nối mạng nội bộ hoặc VPN trước khi truy cập ổ đĩa chia sẻ."
    instruction_spoken: "Trước hết, bạn kiểm tra xem máy tính có đang cắm dây mạng công ty hoặc đang bật kết nối VPN nội bộ không nhé."
    expected_confirmation:
      - "đang bật vpn rồi"
      - "đang cắm mạng công ty rồi"
      - "có mạng nội bộ rồi"
      - "xong rồi"
    fallback_instruction: "Ổ đĩa chia sẻ nội bộ không thể truy cập từ mạng Internet thông thường ở nhà nếu chưa kết nối qua VPN."
    shortcut: "Check VPN Status == Connected"
  - step_id: 2
    action: "Xóa thông tin xác thực ổ mạng cũ bị kẹt bằng net use /delete."
    instruction_spoken: "Bạn mở Command Prompt lên, gõ lệnh: net use sao xẹc delete rồi gõ Y để xác nhận xóa các kết nối ổ đĩa cũ bị lưu sai nhé."
    expected_confirmation:
      - "đã xóa kết nối cũ"
      - "the command completed successfully"
      - "đã xóa xong"
      - "xong rồi"
    fallback_instruction: "Lệnh đầy đủ là n e t cách u s e cách dấu sao cách xẹc d e l e t e."
    shortcut: "cmd -> net use * /delete /y"
  - step_id: 3
    action: "Kết nối lại ổ mạng với tài khoản Domain chuẩn qua lệnh net use hoặc Map Network Drive."
    instruction_spoken: "Bây giờ bạn mở Run gõ dấu hai xẹc ngược rồi đến tên máy chủ chia sẻ, ví dụ hai xẹc file server, sau đó nhập tài khoản domain của bạn để vào lại nhé."
    expected_confirmation:
      - "đã mở được thư mục"
      - "thấy dữ liệu rồi"
      - "vào được ổ chung rồi"
    fallback_instruction: "Nếu hệ thống báo Access is denied, nhóm quyền trên máy chủ của bạn có thể cần được Trưởng phòng phê duyệt lại qua ticket IT."
    shortcut: 'Win + R -> \\fileserver.corp\share'
---
# Xử Lý Sự Cố Truy Cập Ổ Đĩa Mạng Chia Sẻ (Shared Drive Access Denied)
