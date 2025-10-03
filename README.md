# WinMaster V1.0 - Ultimate Task Manager

WinMaster, Windows kullanıcıları için geliştirilmiş, güçlü ve kapsamlı bir **görev yöneticisi ve sistem izleme aracı**dır. Bu araç sayesinde sistem kaynaklarınızı izleyebilir, çalışan süreçleri yönetebilir, başlangıç programlarını kontrol edebilir, servisleri yönetebilir ve sistem bilgilerini görüntüleyebilirsiniz. Ayrıca yüklü programları kaldırabilir ve artık dosyalarını silebilirsiniz.

---

## Özellikler

- **Gerçek Zamanlı Kaynak İzleme:**
  - CPU, RAM, Disk, Ağ, GPU kullanımı
  - GPU sıcaklığı ve fan hızı

- **Süreç Yönetimi (Processes):**
  - Çalışan uygulamaları ve süreçleri görüntüleme
  - Süreçleri sonlandırma
  - Google araması ile hızlı araştırma

- **Başlangıç Uygulamaları (Startup Apps):**
  - Başlangıçta çalışan programları listeleme
  - Programları devre dışı bırakma, etkinleştirme veya silme
  - İlgili süreci anında sonlandırma

- **Servis Yönetimi (Services):**
  - Servislerin durumunu görüntüleme
  - Servisleri başlatma, durdurma ve yeniden başlatma

- **Sistem Bilgisi (System Info):**
  - Anakart, CPU, RAM, GPU, Disk ve Ağ bilgilerini görüntüleme

- **Yüklü Programlar (Installed Programs):**
  - Programları listeleme ve filtreleme
  - Programları kaldırma ve artık dosyalarını silme

---

## Gereksinimler

- Python 3.10 veya üzeri
- Windows işletim sistemi
- Python kütüphaneleri:
  - `psutil`
  - `GPUtil`
  - `PyQt6`
  - `pyqtgraph`

Kurulum:

```bash
pip install psutil GPUtil PyQt6 pyqtgraph
