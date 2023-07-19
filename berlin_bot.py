import time
import os
import logging
from platform import system
import datetime

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

system = system()

logging.basicConfig(
    format='%(asctime)s\t%(levelname)s\t%(message)s',
    level=logging.INFO,
)

class WebDriver:
    def __init__(self):
        self._driver: webdriver.Chrome
        self._implicit_wait_time = 20

    def __enter__(self) -> webdriver.Chrome:
        logging.info("Open browser")
        # some stuff that prevents us from being locked out
        options = webdriver.ChromeOptions() 
        options.add_argument('--disable-blink-features=AutomationControlled')
        self._driver = webdriver.Chrome(options=options)
        self._driver.implicitly_wait(self._implicit_wait_time) # seconds
        self._driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self._driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.53 Safari/537.36'})
        return self._driver

    def __exit__(self, exc_type, exc_value, exc_tb):
        logging.info("Close browser")
        self._driver.quit()

class BerlinBot:
    def __init__(self):
        self.wait_time = 40
        self._sound_file = os.path.join(os.getcwd(), "alarm.wav")
        self._error_message = "There are currently no dates available for the selected service! Please try again later."
        self._token_error_message = "Vielen Dank für die Nutzung der Landesamt für Einwanderung - Terminvereinbarung! Ihre Sitzung wurde beendet."

    @staticmethod
    def enter_start_page(driver: webdriver.Chrome):
        logging.info("Visit start page")
        driver.get("https://otv.verwalt-berlin.de/ams/TerminBuchen?lang=en")
        driver.find_element(By.XPATH, '//*[@id="mainForm"]/div/div/div/div/div/div/div/div/div/div[1]/div[1]/div[2]/a').click()
        time.sleep(5)

    def tick_off_some_bullshit(self, driver: webdriver.Chrome):
        logging.info("Ticking off agreement")
        driver.find_element(By.XPATH, '//*[@id="xi-div-1"]/div[4]/label[2]/p').click()
        time.sleep(1)
        driver.find_element(By.ID, 'applicationForm:managedForm:proceed').click()
        time.sleep(40)

    def enter_form(self, driver: webdriver.Chrome):
        logging.info("Fill out form")
        # select china
        s = Select(driver.find_element(By.ID, 'xi-sel-400'))
        s.select_by_visible_text("Turkey")
        # eine person
        s = Select(driver.find_element(By.ID, 'xi-sel-422'))
        s.select_by_visible_text("one person")
        # no family
        s = Select(driver.find_element(By.ID, 'xi-sel-427' ))
        s.select_by_visible_text("no")
        time.sleep(5)


        driver.find_element(By.CSS_SELECTOR, '.kachel-163-0-1 p').click()
        time.sleep(2)

        driver.find_element(By.CSS_SELECTOR, '.accordion-163-0-1-1 > label').click()
        time.sleep(2)

        driver.find_element(By.CSS_SELECTOR, '.level3:nth-child(6) > label').click()
        time.sleep(10)

        driver.find_element(By.ID, 'applicationForm:managedForm:proceed').click()
        time.sleep(self.wait_time)
    
    def _success(self, driver: webdriver.Chrome):
        logging.info("!!!SUCCESS - do not close the window!!!!")
        while True:
            self._play_sound_osx(self._sound_file)
            time.sleep(20)
            if self._error_message in driver.page_source:
                break



    def run_once(self):
        with WebDriver() as driver:
            self.enter_start_page(driver)
            self.tick_off_some_bullshit(driver)
            self.enter_form(driver)

            # retry submit
            for _ in range(90):
                if self._token_error_message in driver.page_source:
                    logging.info("Expired Token...")
                    break
        
                if not self._error_message in driver.page_source:
                    self._success(driver)

                logging.info("Retry submitting form")
                driver.find_element(By.ID, 'applicationForm:managedForm:proceed').click()
                time.sleep(self.wait_time)

    def run_loop(self):
        while True:
            logging.info("One more round")
            self.run_once()
            time.sleep(self.wait_time)

    # stolen from https://github.com/JaDogg/pydoro/blob/develop/pydoro/pydoro_core/sound.py
    @staticmethod
    def _play_sound_osx(sound, block=True):
        """
        Utilizes AppKit.NSSound. Tested and known to work with MP3 and WAVE on
        OS X 10.11 with Python 2.7. Probably works with anything QuickTime supports.
        Probably works on OS X 10.5 and newer. Probably works with all versions of
        Python.
        Inspired by (but not copied from) Aaron's Stack Overflow answer here:
        http://stackoverflow.com/a/34568298/901641
        I never would have tried using AppKit.NSSound without seeing his code.
        """
        from AppKit import NSSound
        from Foundation import NSURL
        from time import sleep

        logging.info("Play sound")
        if "://" not in sound:
            if not sound.startswith("/"):
                from os import getcwd

                sound = getcwd() + "/" + sound
            sound = "file://" + sound
        url = NSURL.URLWithString_(sound)
        nssound = NSSound.alloc().initWithContentsOfURL_byReference_(url, True)
        if not nssound:
            raise IOError("Unable to load sound named: " + sound)
        nssound.play()

        if block:
            sleep(nssound.duration())

if __name__ == "__main__":
    BerlinBot().run_loop()
