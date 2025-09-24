#!/usr/bin/env python3
"""
Instagram парсер на Selenium WebDriver
Получает данные напрямую из браузера без ограничений API
"""

import os
import time
import json
import requests
from datetime import datetime
from typing import List, Dict, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from dotenv import load_dotenv
import pymongo

# Загружаем переменные окружения
load_dotenv()
load_dotenv('mongodb_config.env')

class InstagramSeleniumParser:
    def __init__(self, mongodb_uri: str = None):
        """Инициализация парсера"""
        self.mongodb_uri = mongodb_uri or os.getenv('MONGODB_URI', 'mongodb://trend_ai_user:|#!x1K52H.0{8d3@localhost:27017/instagram_gallery')
        self.driver = None
        self.wait = None
        self.client = None
        self.db = None
        self.collection = None
        
    def setup_driver(self, headless: bool = True) -> bool:
        """Настройка Chrome WebDriver"""
        try:
            chrome_options = Options()
            
            if headless:
                chrome_options.add_argument("--headless")
            
            # Настройки для стабильности
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            
            # Отключаем изображения для ускорения
            prefs = {
                "profile.managed_default_content_settings.images": 2,
                "profile.default_content_setting_values.notifications": 2
            }
            chrome_options.add_experimental_option("prefs", prefs)
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.wait = WebDriverWait(self.driver, 10)
            
            print("✅ Chrome WebDriver настроен")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка настройки WebDriver: {e}")
            return False
    
    def connect_mongodb(self) -> bool:
        """Подключение к MongoDB"""
        try:
            self.client = pymongo.MongoClient(self.mongodb_uri)
            self.db = self.client["instagram_gallery"]
            self.collection = self.db["images"]
            
            # Проверяем подключение
            self.client.admin.command('ping')
            print("✅ Подключение к MongoDB установлено")
            return True
        except Exception as e:
            print(f"❌ Ошибка подключения к MongoDB: {e}")
            return False
    
    def login_instagram(self, username: str, password: str) -> bool:
        """Авторизация в Instagram"""
        try:
            print(f"🔐 Авторизация в Instagram...")
            
            # Переходим на страницу входа
            self.driver.get("https://www.instagram.com/accounts/login/")
            time.sleep(3)
            
            # Вводим логин
            username_input = self.wait.until(
                EC.presence_of_element_located((By.NAME, "username"))
            )
            username_input.clear()
            username_input.send_keys(username)
            
            # Вводим пароль
            password_input = self.driver.find_element(By.NAME, "password")
            password_input.clear()
            password_input.send_keys(password)
            
            # Нажимаем кнопку входа
            login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            login_button.click()
            
            # Ждем загрузки главной страницы
            time.sleep(5)
            
            # Проверяем успешность входа
            if "instagram.com" in self.driver.current_url and "login" not in self.driver.current_url:
                print("✅ Авторизация успешна")
                return True
            else:
                print("❌ Ошибка авторизации")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка авторизации: {e}")
            return False
    
    def parse_account(self, username: str, posts_limit: int = 100) -> List[Dict]:
        """Парсинг аккаунта Instagram"""
        try:
            print(f"🔍 Парсинг аккаунта: @{username}")
            
            # Переходим на страницу аккаунта
            profile_url = f"https://www.instagram.com/{username}/"
            self.driver.get(profile_url)
            time.sleep(3)
            
            # Проверяем существование аккаунта
            if "Page Not Found" in self.driver.page_source:
                print(f"❌ Аккаунт @{username} не найден")
                return []
            
            # Получаем информацию о профиле
            profile_info = self.get_profile_info()
            
            # Получаем посты
            posts = self.get_posts(posts_limit)
            
            print(f"✅ Найдено {len(posts)} постов")
            return posts
            
        except Exception as e:
            print(f"❌ Ошибка парсинга аккаунта: {e}")
            return []
    
    def get_profile_info(self) -> Dict:
        """Получение информации о профиле"""
        try:
            profile_info = {}
            
            # Имя пользователя
            try:
                username_element = self.driver.find_element(By.XPATH, "//h2[contains(@class, 'x1lliihq')]")
                profile_info["username"] = username_element.text
            except:
                profile_info["username"] = "N/A"
            
            # Количество постов
            try:
                posts_count_element = self.driver.find_element(By.XPATH, "//span[contains(text(), 'posts')]/span")
                profile_info["posts_count"] = posts_count_element.text
            except:
                profile_info["posts_count"] = "N/A"
            
            # Количество подписчиков
            try:
                followers_element = self.driver.find_element(By.XPATH, "//span[contains(text(), 'followers')]/span")
                profile_info["followers_count"] = followers_element.text
            except:
                profile_info["followers_count"] = "N/A"
            
            # Количество подписок
            try:
                following_element = self.driver.find_element(By.XPATH, "//span[contains(text(), 'following')]/span")
                profile_info["following_count"] = following_element.text
            except:
                profile_info["following_count"] = "N/A"
            
            return profile_info
            
        except Exception as e:
            print(f"❌ Ошибка получения информации о профиле: {e}")
            return {}
    
    def get_posts(self, posts_limit: int) -> List[Dict]:
        """Получение постов аккаунта"""
        try:
            posts = []
            posts_loaded = 0
            
            # Прокручиваем страницу для загрузки постов
            while posts_loaded < posts_limit:
                # Находим все посты на странице
                post_elements = self.driver.find_elements(By.XPATH, "//article//a[contains(@href, '/p/')]")
                
                if len(post_elements) > posts_loaded:
                    # Обрабатываем новые посты
                    for i in range(posts_loaded, min(len(post_elements), posts_limit)):
                        post_url = post_elements[i].get_attribute("href")
                        if post_url and post_url not in [p.get("url", "") for p in posts]:
                            post_data = self.get_post_data(post_url)
                            if post_data:
                                posts.append(post_data)
                                posts_loaded += 1
                                print(f"📸 Обработан пост {posts_loaded}/{posts_limit}")
                
                # Прокручиваем вниз
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                
                # Проверяем, есть ли еще посты
                if len(post_elements) == posts_loaded:
                    break
            
            return posts
            
        except Exception as e:
            print(f"❌ Ошибка получения постов: {e}")
            return []
    
    def get_post_data(self, post_url: str) -> Optional[Dict]:
        """Получение данных конкретного поста"""
        try:
            # Переходим на страницу поста
            self.driver.get(post_url)
            time.sleep(2)
            
            post_data = {
                "url": post_url,
                "timestamp": datetime.now().isoformat(),
                "images": [],
                "likes": 0,
                "comments": 0,
                "caption": "",
                "hashtags": []
            }
            
            # Получаем изображения
            images = self.get_post_images()
            post_data["images"] = images
            
            # Получаем количество лайков
            try:
                likes_element = self.driver.find_element(By.XPATH, "//span[contains(@class, 'html-span')]")
                likes_text = likes_element.text
                if "likes" in likes_text:
                    post_data["likes"] = int(likes_text.split()[0].replace(",", ""))
            except:
                pass
            
            # Получаем описание поста
            try:
                caption_element = self.driver.find_element(By.XPATH, "//div[contains(@class, 'x1lliihq')]//span")
                caption = caption_element.text
                post_data["caption"] = caption
                
                # Извлекаем хештеги
                hashtags = [tag for tag in caption.split() if tag.startswith("#")]
                post_data["hashtags"] = hashtags
            except:
                pass
            
            return post_data
            
        except Exception as e:
            print(f"❌ Ошибка получения данных поста: {e}")
            return None
    
    def get_post_images(self) -> List[str]:
        """Получение URL изображений поста"""
        try:
            images = []
            
            # Ищем все изображения в посте
            img_elements = self.driver.find_elements(By.XPATH, "//img[contains(@src, 'instagram.com')]")
            
            for img in img_elements:
                src = img.get_attribute("src")
                if src and "instagram.com" in src:
                    # Очищаем URL от параметров
                    clean_url = src.split("?")[0]
                    if clean_url not in images:
                        images.append(clean_url)
            
            return images
            
        except Exception as e:
            print(f"❌ Ошибка получения изображений: {e}")
            return []
    
    def download_images(self, posts: List[Dict], download_dir: str = "images") -> List[Dict]:
        """Скачивание изображений"""
        try:
            if not os.path.exists(download_dir):
                os.makedirs(download_dir)
            
            downloaded_images = []
            
            for post in posts:
                for i, img_url in enumerate(post["images"]):
                    try:
                        # Генерируем имя файла
                        filename = f"{post['url'].split('/')[-2]}_{i+1}.jpg"
                        filepath = os.path.join(download_dir, filename)
                        
                        # Скачиваем изображение
                        response = requests.get(img_url, timeout=30)
                        if response.status_code == 200:
                            with open(filepath, 'wb') as f:
                                f.write(response.content)
                            
                            downloaded_images.append({
                                "url": img_url,
                                "local_filename": filename,
                                "local_path": filepath,
                                "file_size": len(response.content),
                                "downloaded_at": datetime.now().isoformat()
                            })
                            
                            print(f"⬇️ Скачано: {filename}")
                        
                    except Exception as e:
                        print(f"❌ Ошибка скачивания {img_url}: {e}")
            
            return downloaded_images
            
        except Exception as e:
            print(f"❌ Ошибка скачивания изображений: {e}")
            return []
    
    def save_to_mongodb(self, posts: List[Dict], downloaded_images: List[Dict]) -> bool:
        """Сохранение данных в MongoDB"""
        try:
            for post in posts:
                for img_data in downloaded_images:
                    if img_data["url"] in post["images"]:
                        doc = {
                            "url": img_data["url"],
                            "post_url": post["url"],
                            "publication_date": post["timestamp"],
                            "likes": post["likes"],
                            "comments": post["comments"],
                            "caption": post["caption"],
                            "hashtags": post["hashtags"],
                            "account_name": post.get("username", "N/A"),
                            "local_filename": img_data["local_filename"],
                            "local_path": img_data["local_path"],
                            "file_size": img_data["file_size"],
                            "downloaded_at": img_data["downloaded_at"],
                            "full_image_url": f"http://158.160.19.119/images/{img_data['local_filename']}"
                        }
                        
                        self.collection.insert_one(doc)
            
            print(f"✅ Сохранено {len(downloaded_images)} изображений в MongoDB")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка сохранения в MongoDB: {e}")
            return False
    
    def run_full_parsing(self, username: str, password: str, posts_limit: int = 100) -> bool:
        """Запуск полного парсинга"""
        try:
            print(f"🚀 ЗАПУСК ПОЛНОГО ПАРСИНГА ДЛЯ @{username}")
            print("=" * 60)
            
            # Настройка WebDriver
            if not self.setup_driver():
                return False
            
            # Подключение к MongoDB
            if not self.connect_mongodb():
                return False
            
            # Авторизация
            if not self.login_instagram(username, password):
                return False
            
            # Парсинг аккаунта
            posts = self.parse_account(username, posts_limit)
            if not posts:
                return False
            
            # Скачивание изображений
            downloaded_images = self.download_images(posts)
            if not downloaded_images:
                return False
            
            # Сохранение в MongoDB
            if not self.save_to_mongodb(posts, downloaded_images):
                return False
            
            print("🎉 ПАРСИНГ ЗАВЕРШЕН УСПЕШНО!")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка полного парсинга: {e}")
            return False
        finally:
            if self.driver:
                self.driver.quit()
            if self.client:
                self.client.close()

if __name__ == "__main__":
    parser = InstagramSeleniumParser()
    
    # Настройки
    username = input("👤 Введите имя пользователя Instagram: ").strip()
    password = input("🔐 Введите пароль Instagram: ").strip()
    posts_limit = int(input("📥 Лимит постов (Enter для 100): ") or "100")
    
    # Запуск парсинга
    parser.run_full_parsing(username, password, posts_limit)


