# MADSET — Advise Eval Lab Final Raporu v1.1

**Tarih:** 26 Ekim 2026  
**Kapsam:** Yalnız sentetik reklam hesabı verilerinden yazılı öneri üreten çevrimdışı eval laboratuvarı.

## 1. Yönetici özeti

Laboratuvar çalışır ve tekrar üretilebilirdir. 30 geliştirme, ilk 10 test ve sonradan dondurulan 12 yeni kör test senaryosu bulunur. Sistem gerçek müşteri verisi, reklam platformu API'si veya otomatik bütçe değişikliği kullanmaz.

Üç deterministik örnek öneri sürümü ölçülmüştür. İlk 40 vakalık demo setinde V1 %0, V2 geliştirmede %63,3 ve V3 %100 geçiş elde etmiştir. Bu ilk test seti geliştirme sürecinde görülmüş olduğundan genellenebilirlik kanıtı değildir.

V3 tamamlandıktan sonra 12 yeni vaka ve beklentileri SHA-256 ile dondurulmuş, üretici değiştirilmeden V1/V2/V3 üçer kez çalıştırılmıştır. Yeni kör sette V1 %0, V2 %0, V3 ilk grader ile %66,7 geçmiştir. Kör koşu bir grader yanlış alarmı ortaya çıkarmıştır: "garanti kullanmayın" uyarısı garanti iddiası sanılmıştır. Üretici tekrar çağrılmadan aynı transcript grader 1.1 ile yeniden puanlanmış ve V3 %75'e çıkmıştır.

Sonuç: mühendislik laboratuvarı ve bağımsız kör doğrulama tamamlanmıştır. Gerçek Madset ürününün yayın onayı için iki bağımsız insan uzman etiketi, gerçek üretim adapteri ve üretim sonrası etki doğrulaması hâlâ gereklidir.

## 2. Veri kümesi ve yöntem

- Geliştirme seti: 30 vaka.
- İlk holdout: 10 vaka; demo sonrasında tüketilmiş sayılır.
- Holdout v2: 12 yeni vaka; girdi ve gold dosyaları final koşudan önce hash ile dondurulmuştur.
- Kapsam: sağlıklı hesap, erken dönem, ölçüm sorunu, performans teşhisi, kontrollü aksiyon, çelişkili sinyal, platform kısıtı ve sınır durumları.
- Her öneri üreticisi yalnız sentetik `input` nesnesini görür; ID, split ve gold beklenti verilmez.
- Her koşu senaryo girdisini, ham çıktıyı, puanı, kritik hatayı, süreyi, model/rules/rubric/grader sürümünü ve biliniyorsa token/maliyeti saklar.

Rubric yedi boyuttan oluşur: veri-matematik, teşhis, kanıt-belirsizlik, stratejik uygunluk, ticari risk, uygulanabilirlik ve sadelik. Geçiş için en az 80/100, kabul edilebilir karar, sıfır kritik hata, en az %75 senaryoya özgü kavram kapsaması, karar-protokolü ve grounded evidence gerekir.

## 3. Ölçülen sürümler

| Set | Sürüm | Geçiş | Karar doğruluğu | Yorum |
|---|---|---:|---:|---|
| Dev, 30 x 3 | V1 | 0/90 (%0) | %13,3 | Tıklama odaklı zayıf başlangıç |
| Dev, 30 x 3 | V2 | 15/90 (%16,7) | %63,3 | Kararlar ilerledi; semantik kapsama çoğu vakada eksik |
| Dev, 30 x 3 | V3 | 90/90 (%100) | %100 | Genellenmiş bağlam, huni ve kontrollü test kuralları |
| İlk holdout, 10 x 3 | V1 | 0/30 (%0) | %10 | Grader 1.1 ile tüketilmiş eski test |
| İlk holdout, 10 x 3 | V2 | 0/30 (%0) | %30 | Grader 1.1 ile tüketilmiş eski test |
| İlk holdout, 10 x 3 | V3 | 24/30 (%80) | %90 | Grader 1.1 ile tüketilmiş eski test |
| Yeni kör holdout, 12 x 3 | V1 | 0/36 (%0) | %8,3 | Final tek koşu |
| Yeni kör holdout, 12 x 3 | V2 | 0/36 (%0) | %41,7 | Daha sıkı semantik kapı |
| Yeni kör holdout, 12 x 3 | V3 | 27/36 (%75) | %83,3 | Aynı transcript, grader 1.1 |

V3, V1'e göre yeni kör sette +75 yüzde puan ilerlemiştir. Deterministik sürümlerde üç tekrar aynı sonucu vermiştir; bu gerçek LLM non-determinizmini kanıtlamaz.

## 4. Hata analizi

Yeni kör sette V3'ün üç gerçek hata türü görünür kalmıştır:

1. **ADV-041 — gecikmeli randevu bağlamı:** Doğru WAIT kararı verildi, ancak öneri gecikmeli randevu geri dönüşünü yeterince kapsamadı.
2. **ADV-044 — iyi CPA, eksik net ekonomi:** Sistem marj belirsizliğini görünce DIAGNOSE seçti; gold, hedef altındaki satış CPA nedeniyle ihtiyatlı MAINTAIN bekliyordu.
3. **ADV-049 — iptal bilgisi:** Sistem bağlamdaki "Purchase" ifadesini ölçüm sorunu saydı; gold, brüt/net satış ve iptal nedenlerini inceleyen DIAGNOSE bekliyordu.

Bu hatalar kör sonuç görüldükten sonra V3'e geri beslenmemiştir. Gelecek V4 çalışması bu vakaları geliştirme girdisine dönüştürürse yeni bir holdout gerektirir.

## 5. Grader güvenilirliği

Grader 8 hedefli negatif mutasyonun tamamını yakalamış, 19 pozitif kontrolde yanlış alarm üretmemiştir. Pozitif set; temkinli ACT örneklerini, "garanti değildir" ve "garanti kullanmayın" gibi olumsuz bağlamları kapsar.

Bu ölçüm küçük ve el yapımıdır. Tam Türkçe anlam doğruluğunu veya stratejik uzmanlığı kanıtlamaz. İki uzman için kör değerlendirme CSV'si hazırlanmıştır; her satır senaryo ve öneri metnini içerir, otomatik puan son sütunda gizlenebilir. İnsan etiketleri girildiğinde analiz komutu gözlenen uyumu, Cohen kappa'yı ve otomatik grader'ın konsensüse göre recall/yanlış-alarm oranını hesaplar.

İnsan etiketi henüz bulunmadığından uzman uyumu ve gerçek grader kalibrasyonu tamamlandı sayılamaz. Claude LLM-judge adaptörü hazırdır ancak gerçek anahtarla ölçülmemiş ve insan etiketlerine karşı kalibre edilmemiştir; dolayısıyla LLM-judge güvenilirliği iddia edilmez.

## 6. Maliyet ve operasyon

V1/V2/V3 yerel Python kurallarıdır; API maliyeti 0 USD'dir. Harici adapter gerçek model adı, model sürümü, prompt sürümü ve token kullanımını kaydedebilir. Kullanıcı güncel sağlayıcı fiyatlarını ortam değişkenleriyle sabitlerse tahmini maliyet hesaplanır; aksi halde maliyet `null` kalır.

Eski `outputs/claude_v1` kaydı başarılı model ölçümü değildir: API anahtarı olmadığı için 30/30 producer error oluşmuştur. Bu kayıt üç başarılı iterasyon arasında sunulmamalıdır.

## 7. Teslimat ve açık kapılar

**Tamamlanan:** tek komut eval, 52 sentetik vaka, iki ayrı holdout dalgası, gold izolasyonu, şema doğrulama, yedi boyutlu rubric, sekiz kritik hata, semantik kapsama kapısı, 35 anahtarsız test, isteğe bağlı Claude LLM yargıç adaptörü, trial-bazlı kayıt ve karşılaştırma, yeniden puanlama, JSON/CSV/HTML raporlama, kör uzman inceleme paketi ve 15 dakikalık demo akışı.

**Dış bağımlılık:** iki bağımsız uzman, hazırlanan kör CSV'yi doldurmalı; uyuşmazlıklar üçüncü değerlendirme ile kapatılmalıdır.

**Ürün bağımlılığı:** gerçek Madset öneri motoru sentetik-input adapterine bağlanmalı, token/maliyet kayıtları doğrulanmalı ve yeni bir kör holdout üzerinde ölçülmelidir.

**Üretim bağımlılığı:** sentetik eval geçişi satış veya kârlılık artışını kanıtlamaz. Üretim izleme, kullanıcı geri bildirimi ve uygun olduğunda A/B sonucu ayrı katmanlardır.

## 8. Nihai karar

Advise Eval Lab teknik teslimata hazırdır ve ilk sürüme göre sayısal iyileşmeyi yeni kör sette göstermektedir. V3, kör sette %75 geçişle gerçek hata bırakmış; bu sonuç eski %100 demo skorundan daha güvenilir ve daha faydalıdır. İnsan uzman kalibrasyonu tamamlanmadan gerçek Madset ürünü için "yayına hazır" kararı verilmemelidir.
