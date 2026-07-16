import os
import time
import random
import schedule
from datetime import datetime
import requests

# Playwright'ı içe aktar
from playwright.sync_api import sync_playwright

# ============= AYARLAR =============
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
INTERVAL_HOURS = int(os.getenv("CHECK_INTERVAL_HOURS", 12))

class SocialMediaKeeper:
    def __init__(self):
        self.results = {}
        
    def send_telegram(self, message):
        """Telegram'a mesaj gönder"""
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            payload = {
                "chat_id": TELEGRAM_CHAT_ID,
                "text": message,
                "parse_mode": "HTML"
            }
            response = requests.post(url, json=payload, timeout=30)
            print(f"📨 Telegram gönderildi: {response.status_code}")
        except Exception as e:
            print(f"❌ Telegram hatası: {e}")

    def human_delay(self, min_sec=1, max_sec=3):
        """İnsan gibi rastgele bekle"""
        time.sleep(random.uniform(min_sec, max_sec))

    def do_human_activity(self, page, duration):
        """Sayfada rastgele gezin"""
        start_time = time.time()
        
        def click_random_link():
            links = page.query_selector_all('a[href]')
            if links and len(links) > 3:
                try:
                    random.choice(links[:20]).click()
                    self.human_delay(2, 4)
                    page.go_back()
                except:
                    pass
        
        while time.time() - start_time < duration:
            action = random.choice([
                lambda: page.evaluate(f"window.scrollBy(0, {random.randint(100, 500)})"),
                lambda: page.mouse.move(random.randint(100, 800), random.randint(100, 600)),
                click_random_link,
                lambda: self.human_delay(0.5, 1.5)
            ])
            action()
            self.human_delay(0.3, 1.0)
    
    def login_facebook(self, page, email, password):
        try:
            page.goto("https://www.facebook.com/")
            self.human_delay(2, 4)
            page.fill('input[name="email"]', email)
            page.fill('input[name="pass"]', password)
            page.click('button[name="login"]')
            self.human_delay(3, 5)
            return True
        except Exception as e:
            return False
    
    def login_instagram(self, page, username, password):
        try:
            page.goto("https://www.instagram.com/accounts/login/")
            self.human_delay(2, 4)
            page.fill('input[name="username"]', username)
            page.fill('input[name="password"]', password)
            page.click('button[type="submit"]')
            self.human_delay(4, 6)
            try:
                page.click('button:has-text("Şimdi değil")')
            except:
                pass
            return True
        except Exception as e:
            return False
    
    def login_google(self, page, email, password):
        try:
            page.goto("https://accounts.google.com/signin")
            self.human_delay(2, 4)
            page.fill('input[type="email"]', email)
            page.click('button:has-text("İleri")')
            self.human_delay(2, 4)
            page.fill('input[type="password"]', password)
            page.click('button:has-text("İleri")')
            self.human_delay(3, 5)
            return True
        except Exception as e:
            return False
    
    def login_tiktok(self, page, username, password):
        try:
            page.goto("https://www.tiktok.com/login")
            self.human_delay(2, 4)
            try:
                page.click('a:has-text("Telefon / e-posta")')
            except:
                page.click('div:has-text("Telefon / e-posta")')
            self.human_delay(1, 2)
            page.fill('input[placeholder="E-posta / Kullanıcı adı"]', username)
            page.fill('input[placeholder="Şifre"]', password)
            page.click('button:has-text("Giriş")')
            self.human_delay(3, 5)
            return True
        except Exception as e:
            return False
    
    def check_platform(self, platform_name, email, password, login_func):
        """Tek bir platformu kontrol et"""
        print(f"\n🔄 {platform_name.upper()} kontrol ediliyor...")
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=True,
                    args=['--disable-blink-features=AutomationControlled']
                )
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                )
                page = context.new_page()
                
                success = login_func(page, email, password)
                
                if success:
                    duration = random.randint(30, 90)
                    print(f"   👤 {duration} saniye geziniyor...")
                    self.do_human_activity(page, duration)
                    browser.close()
                    return "✅ Başarılı"
                else:
                    browser.close()
                    return "❌ Giriş başarısız"
                    
        except Exception as e:
            return f"❌ Hata: {str(e)[:50]}"
    
    def run_all(self):
        """Tüm platformları kontrol et"""
        print("\n" + "="*50)
        print(f"🚀 BAŞLANGIÇ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*50)
        
        platforms = [
            ("Facebook", os.getenv("FACEBOOK_EMAIL"), os.getenv("FACEBOOK_PASSWORD"), self.login_facebook),
            ("YouTube", os.getenv("YOUTUBE_EMAIL"), os.getenv("YOUTUBE_PASSWORD"), self.login_google),
            ("Instagram", os.getenv("INSTAGRAM_USERNAME"), os.getenv("INSTAGRAM_PASSWORD"), self.login_instagram),
            ("TikTok", os.getenv("TIKTOK_USERNAME"), os.getenv("TIKTOK_PASSWORD"), self.login_tiktok),
            ("Gmail", os.getenv("GMAIL_EMAIL"), os.getenv("GMAIL_PASSWORD"), self.login_google),
        ]
        
        results = {}
        for name, email, password, login_func in platforms:
            if not email or not password:
                results[name] = "⚠️ Bilgi eksik"
                continue
            status = self.check_platform(name, email, password, login_func)
            results[name] = status
        
        # Rapor hazırla
        report = "📊 <b>Sosyal Medya Kontrol Raporu</b>\n"
        report += f"🕐 {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
        report += "-"*20 + "\n"
        
        for name, status in results.items():
            emoji = "✅" if "Başarılı" in status else "❌" if "Başarısız" in status else "⚠️"
            report += f"{emoji} <b>{name}</b>: {status}\n"
        
        report += "-"*20 + "\n"
        report += f"⏰ Her {INTERVAL_HOURS} saatte bir kontrol edilecek."
        
        print("\n📊 RAPOR:")
        print(report)
        self.send_telegram(report)
        
        return results
    
    def schedule_run(self):
        """Zamanlanmış çalıştırma"""
        self.run_all()
        schedule.every(INTERVAL_HOURS).hours.do(self.run_all)
        print(f"\n⏰ Bot her {INTERVAL_HOURS} saatte bir çalışacak.")
        
        while True:
            schedule.run_pending()
            time.sleep(60)

# ============= ÇALIŞTIR =============
if __name__ == "__main__":
    print("🚀 Sosyal Medya Canlı Tutma Botu Başlatılıyor...")
    bot = SocialMediaKeeper()
    bot.schedule_run()
