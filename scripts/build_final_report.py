"""Build the checked-in Advise Eval Lab final PDF."""
from pathlib import Path
import sys
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from madset_eval.rubric import PASS_THRESHOLD, RUBRIC, RUBRIC_VERSION
OUT=ROOT/'docs/FINAL_REPORT.pdf'
TEST_COUNT=unittest.defaultTestLoader.discover(str(ROOT/'tests')).countTestCases()

regular=Path(r'C:\Windows\Fonts\arial.ttf')
bold=Path(r'C:\Windows\Fonts\arialbd.ttf')
pdfmetrics.registerFont(TTFont('Arial',str(regular)))
pdfmetrics.registerFont(TTFont('Arial-Bold',str(bold)))

INK=colors.HexColor('#1b2a27');MUTED=colors.HexColor('#626866');ACCENT=colors.HexColor('#edae32')
PALE=colors.HexColor('#f4f3ef');WHITE=colors.white

styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='TitleX',fontName='Arial-Bold',fontSize=28,leading=32,textColor=INK,spaceAfter=8))
styles.add(ParagraphStyle(name='Kicker',fontName='Arial-Bold',fontSize=9,leading=12,textColor=ACCENT,spaceAfter=6))
styles.add(ParagraphStyle(name='Sub',fontName='Arial',fontSize=10,leading=15,textColor=MUTED,spaceAfter=14))
styles.add(ParagraphStyle(name='H1X',fontName='Arial-Bold',fontSize=20,leading=24,textColor=INK,spaceBefore=5,spaceAfter=9))
styles.add(ParagraphStyle(name='H2X',fontName='Arial-Bold',fontSize=13,leading=17,textColor=INK,spaceBefore=7,spaceAfter=5))
styles.add(ParagraphStyle(name='BodyX',fontName='Arial',fontSize=9.3,leading=13.5,textColor=INK,spaceAfter=7))
styles.add(ParagraphStyle(name='SmallX',fontName='Arial',fontSize=7.8,leading=10.5,textColor=MUTED))
styles.add(ParagraphStyle(name='Cell',fontName='Arial',fontSize=7.8,leading=10,textColor=INK))
styles.add(ParagraphStyle(name='CellB',fontName='Arial-Bold',fontSize=7.8,leading=10,textColor=WHITE))

def P(text,style='BodyX'):
    return Paragraph(text,styles[style])

def table(rows,widths,header=True):
    converted=[]
    for i,row in enumerate(rows):
        converted.append([P(str(x),'CellB' if header and i==0 else 'Cell') for x in row])
    t=Table(converted,colWidths=widths,repeatRows=1 if header else 0,hAlign='LEFT')
    commands=[('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),6),
              ('RIGHTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),6),
              ('BOTTOMPADDING',(0,0),(-1,-1),6),('GRID',(0,0),(-1,-1),.25,colors.HexColor('#d7d8d4'))]
    if header:commands += [('BACKGROUND',(0,0),(-1,0),INK)]
    for row in range(1 if header else 0,len(rows)):
        if row%2==0:commands.append(('BACKGROUND',(0,row),(-1,row),PALE))
    t.setStyle(TableStyle(commands));return t

def page(canvas,doc):
    canvas.saveState();w,h=A4
    canvas.setFillColor(ACCENT);canvas.rect(0,h-9*mm,w,9*mm,stroke=0,fill=1)
    canvas.setStrokeColor(colors.HexColor('#d1d3cf'));canvas.line(18*mm,15*mm,w-18*mm,15*mm)
    canvas.setFont('Arial',7.5);canvas.setFillColor(MUTED)
    canvas.drawString(18*mm,9*mm,'MADSET / ADVISE EVAL LAB v1.2')
    canvas.drawRightString(w-18*mm,9*mm,f'27.10.2026  -  {doc.page}/4')
    canvas.restoreState()

story=[]
story += [Spacer(1,9*mm),P('MADSET - ENGINEERING','Kicker'),P('ADVISE EVAL LAB','TitleX'),
          P('Sentetik reklam önerileri için karşılaştırmalı, tekrar üretilebilir değerlendirme sistemi','Sub'),
          P('1 / Yönetici özeti','H1X'),
          P('<b>Teknik teslimat hazırdır.</b> Laboratuvar 30 geliştirme, 10 ilk test ve sonradan dondurulan 12 yeni kör test vakası içerir. Gerçek müşteri verisi, reklam platformu API çağrısı ve otomatik bütçe değişikliği yoktur.'),
          P('Üç yerel kural üreticisi ölçülmüştür. İlk 40 vakalık sette V3 yüzde 100 görünse de bu set geliştirme sürecinde tüketilmiştir. V3 tamamlandıktan sonra yeni 12-vaka seti SHA-256 ile dondurulmuş ve üretici değiştirilmeden final doğrulaması yapılmıştır.'),
          P('2 / Yeni kör doğrulama','H2X')]
story.append(table([
    ['Sürüm','İlk kör sonuç','Grader 1.1','Karar doğruluğu'],
    ['V1','0/36 (%0)','0/36 (%0)','%8,3'],
    ['V2','0/36 (%0)','0/36 (%0)','%41,7'],
    ['V3','24/36 (%66,7)','27/36 (%75)','%83,3'],
],[31*mm,42*mm,42*mm,42*mm]))
story += [Spacer(1,5*mm),P('<b>Yorum:</b> V3, V1\'e göre yeni kör sette +75 yüzde puan ilerlemiştir. İlk kör koşu bir grader yanlış alarmını ortaya çıkardı; üretici tekrar çağrılmadan aynı transcript yeniden puanlandı.'),
          P('<b>Nihai sınır:</b> İnsan uzman kalibrasyonu olmadan gerçek Madset ürünü için yayın onayı verilemez.','SmallX'),PageBreak()]

story += [Spacer(1,7*mm),P('DEĞERLENDİRME MİMARİSİ','TitleX'),
          P('3 / Rubric ve geçiş kapısı','H1X'),
          P('Rubric veri-matematik, teşhis, kanıt-belirsizlik, stratejik uygunluk, ticari risk, uygulanabilirlik ve sadelik boyutlarını 0-4 aralığında puanlar. Kritik hata yüksek puanla telafi edilemez.'),
          table([['Boyut','Ağırlık','4 puan çıpası']]+[[d['name'],str(d['weight']),d['four']] for d in RUBRIC['dimensions']],[42*mm,23*mm,92*mm]),
          Spacer(1,4*mm),P(f'Geçiş: en az {PASS_THRESHOLD:g}/100, kabul edilen karar, sıfır F01-F08/FMT, en az yüzde 75 kavram kapsaması, karar sınıfına uygun protokol ve grounded evidence. Aktif rubrik: {RUBRIC_VERSION}.'),
          P('4 / Harness ve kayıt','H2X'),
          P('Her trial sentetik girdi transcriptini, çıktıyı, gerekçeyi, puanı, semantik kapsama kanıtını, kritik hata kodlarını, süreyi ve sürüm metaverisini saklar. Harici adapter model, prompt, token ve - fiyatlar sabitlenirse - maliyet bilgisini taşır.'),
          P('Karşılaştırma bütün trial\'ları senaryo bazında kullanır. Grader değişiklikleri üreticiyi yeniden çağırmadan <b>regrade</b> ile aynı transcript üzerinde uygulanır; eski sonuç korunur.'),PageBreak()]

story += [Spacer(1,7*mm),P('KÖR SET BULGULARI','TitleX'),P('5 / Gerçek hata türleri','H1X'),
          table([
            ['Vaka','Beklenen','Bulgu'],
            ['ADV-041','WAIT','Gecikmeli randevu geri dönüşü öneride yeterince kapsanmadı.'],
            ['ADV-044','MAINTAIN','Hedef altı satış CPA yerine gereksiz DIAGNOSE seçildi.'],
            ['ADV-049','DIAGNOSE','İptal bilgisi ölçüm arızası gibi yorumlandı.'],
          ],[25*mm,30*mm,102*mm]),
          Spacer(1,5*mm),P('Kör sonuç görüldükten sonra V3 değiştirilmedi. Bu vakalar V4 geliştirmesine alınırsa sonraki kabul için yeni bir holdout oluşturulmalıdır.'),
          P('6 / Grader güvenilirliği','H2X'),
          P('<b>Negatif mutasyon:</b> 8/8 hedef hata yakalandı. <b>Pozitif kontrol:</b> 19/19 doğru kabul edildi; gözlenen yanlış alarm yüzde 0.'),
          P('Kör sette "garanti veya uygunsuz iddia kullanmayın" cümlesi ilk grader tarafından F03 sayıldı. Negasyon bağlamı düzeltildi, regresyon testi eklendi ve mevcut transcript grader 1.1 ile yeniden puanlandı.'),
          P('Bu küçük, el yapımı kontrol kümesi tam Türkçe anlam doğruluğu değildir. Hazır kör CSV iki uzmanın bağımsız overall_pass ve yedi boyut puanı vermesine olanak sağlar. Analiz aracı agreement, Cohen kappa ve grader-vs-consensus recall/yanlış-alarm oranını hesaplar.'),
          P('<b>Claude tekrar güvenilirliği:</b> Aynı 30 öneri üç kez yargılandı. Geçişler %83,33 / %93,33 / %90; 27/30 oybirliği, ortalama ikili anlaşma %93,33 ve Fleiss kappa 0,6625. Değişken vakalar ADV-001, 003 ve 038; çoğunlukta kalanlar ADV-001, 014 ve 017\'dir.'),
          P('Toplam 90 yargı 173.856 girdi + 62.023 çıktı tokenı ve tahmini 1,451913 USD kullandı. Tekrar tutarlılığı ölçülmüştür; insan etiketlerine karşı semantik doğruluk kalibrasyonu hâlâ açıktır.','SmallX'),
          P('<b>Henüz yok:</b> doldurulmuş iki uzman etiketi ve insan etiketlerine karşı kalibre edilmiş LLM judge. Bu nedenle stratejik uzmanlık onaylanmış sayılmaz.','SmallX'),PageBreak()]

story += [Spacer(1,7*mm),P('TESLİMAT VE YAYIN KAPISI','TitleX'),P('7 / Tamamlananlar','H1X'),
          table([
            ['Teslim','Durum'],
            ['52 sentetik vaka; dev + iki holdout dalgası','Tamamlandı'],
            ['Şema, hash doğrulama ve gold izolasyonu','Çalışır'],
            ['Üç sürüm, '+str(TEST_COUNT)+' test, 90-yargı güvenilirliği','Geçti'],
            ['Semantik kapsama + 30-vaka Claude yargısı','Çalışır; insan kalibrasyonu bekliyor'],
            ['Trial-bazlı karşılaştırma ve regrade','Çalışır'],
            ['JSON, CSV, HTML, Markdown ve PDF rapor','Tamamlandı'],
            ['İki uzman için kör değerlendirme paketi','Hazır; insan etiketi yok'],
          ],[99*mm,58*mm]),
          Spacer(1,5*mm),P('8 / Kapanması gereken dış kapılar','H2X'),
          P('<b>İnsan:</b> Reklam/performans uzmanı ile ürün/KOBİ uzmanı kör paketi doldurmalı; uyuşmazlıklar üçüncü değerlendirme ile kapatılmalıdır.'),
          P('<b>Ürün:</b> Gerçek Madset öneri motoru sentetik-input adapterine bağlanmalı; model, prompt, token ve maliyet kaydıyla yeni bir kör sette ölçülmelidir.'),
          P('<b>Üretim:</b> Sentetik eval geçişi satış veya kârlılık artışını kanıtlamaz. Üretim izleme, kullanıcı geri bildirimi ve uygun A/B ölçümü ayrıca gerekir.'),
          P('9 / Nihai karar','H2X'),
          P('<b>Advise Eval Lab teknik teslimata hazırdır.</b> V3, yeni kör sette yüzde 75 geçişle ilk sürümden açıkça iyidir ve üç gerçek hatayı görünür bırakmıştır. İnsan uzman kalibrasyonu tamamlanmadan gerçek ürün için "yayına hazır" denmemelidir.'),
          Spacer(1,3*mm),P('Kaynak dayanağı: Advise Lab gereksinimleri ve kullanıcı tarafından sağlanan AI ajan eval rehberi. Yerel karar sınıfları, ağırlıklar, semantik kavram kuralları ve baseline üreticiler bu laboratuvarın tasarım kararlarıdır.','SmallX')]

doc=SimpleDocTemplate(str(OUT),pagesize=A4,rightMargin=18*mm,leftMargin=18*mm,
                      topMargin=15*mm,bottomMargin=19*mm,title='Madset Advise Eval Lab Final Raporu v1.2')
doc.build(story,onFirstPage=page,onLaterPages=page)
print(OUT)
