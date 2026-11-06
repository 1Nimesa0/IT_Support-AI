---
sop_id: "SOP-NET-001"
title: "Corporate VPN Handshake or Tunnel Negotiation Failure"
category: "Network"
symptoms:
  - "vpn không kết nối được"
  - "vpn handshake failed"
  - "lỗi forticlient hoặc cisco anyconnect"
  - "vpn timeout"
  - "không thể thiết lập đường truyền vpn"
  - "vpn dừng ở 40% hoặc 98%"
prerequisites:
  device_type: ["Windows", "macOS"]
steps:
  - step_id: 1
    action: "Kiểm tra kết nối Internet cơ bản trước khi thiết lập VPN."
    instruction_spoken: "Bạn kiểm tra xem mạng Internet ở nhà có đang lướt web bình thường không nhé, sau đó ngắt kết nối và tắt hẳn ứng dụng VPN đi giúp mình."
    expected_confirmation:
      - "internet bình thường"
      - "đã tắt vpn rồi"
      - "đã đóng ứng dụng vpn"
      - "xong rồi"
    fallback_instruction: "Nhấn chuột phải vào biểu tượng VPN dưới khay đồng hồ và chọn Quit hoặc Exit hoàn toàn."
    shortcut: "Exit VPN Client from System Tray"
  - step_id: 2
    action: "Khởi động lại dịch vụ VPN Adapter hoặc Base Filtering Engine."
    instruction_spoken: "Bạn mở Command Prompt bằng quyền Administrator và gõ lệnh: net stop vpnagent rồi gõ tiếp net start vpnagent để khởi động lại dịch vụ VPN nhé."
    expected_confirmation:
      - "đã khởi động lại dịch vụ"
      - "service started successfully"
      - "xong rồi"
    fallback_instruction: "Nếu dùng FortiClient, bạn chỉ cần mở Task Manager, tìm tiến trình FortiTray và bấm End Task rồi mở lại."
    shortcut: "Admin CMD -> net stop vpnagent && net start vpnagent"
  - step_id: 3
    action: "Thử kết nối lại qua cổng thay thế (SSL-VPN cổng 443 hoặc 10443)."
    instruction_spoken: "Bây giờ bạn mở lại phần mềm VPN, chọn máy chủ dự phòng hoặc cổng 10443 rồi nhập mã OTP mới nhất từ ứng dụng xác thực để kết nối lại nhé."
    expected_confirmation:
      - "vpn đã kết nối thành công"
      - "đã báo 100% connected"
      - "vào được mạng nội bộ rồi"
    fallback_instruction: "Nếu thanh tiến trình dừng ở 98%, hãy kiểm tra xem phần mềm diệt virus hoặc tường lửa gia đình có đang chặn cổng IPsec UDP 500/4500 hay không."
    shortcut: "Reconnect VPN with 10443 / Backup Gateway"
---
# Xử Lý Sự Cố Bắt Tay Kết Nối Mạng Riêng Ảo VPN (VPN Handshake Failure)
