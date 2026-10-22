from __future__ import annotations

import ctypes
import time
from pathlib import Path

from PIL import ImageGrab
import psutil
import win32con
import win32gui
import win32process
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


ROOT = Path(__file__).resolve().parent
SCREENSHOTS = ROOT / "screenshots"
SCREENSHOTS.mkdir(parents=True, exist_ok=True)


def find_window(fragment: str) -> int | None:
    found: list[int] = []
    browser_windows: list[int] = []

    def callback(hwnd: int, _extra: object) -> None:
        if not win32gui.IsWindowVisible(hwnd):
            return
        title = win32gui.GetWindowText(hwnd)
        if "Chrome_WidgetWin" in win32gui.GetClassName(hwnd):
            browser_windows.append(hwnd)
        if fragment.lower() in title.lower():
            found.append(hwnd)

    win32gui.EnumWindows(callback, None)
    return found[0] if found else (browser_windows[-1] if browser_windows else None)


def browser_process_ids(driver: webdriver.Edge) -> set[int]:
    """Return the msedgedriver process and all Edge descendants."""
    process = getattr(driver.service, "process", None)
    if process is None or process.pid is None:
        return set()
    try:
        root = psutil.Process(process.pid)
        return {root.pid, *(child.pid for child in root.children(recursive=True))}
    except (psutil.Error, OSError):
        return {process.pid}


def find_window_for_processes(process_ids: set[int]) -> int | None:
    found: list[int] = []

    def callback(hwnd: int, _extra: object) -> None:
        if not win32gui.IsWindowVisible(hwnd):
            return
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        title = win32gui.GetWindowText(hwnd)
        if pid in process_ids and title:
            found.append(hwnd)

    win32gui.EnumWindows(callback, None)
    return found[0] if found else None


def capture_window(path: Path, title_fragment: str, process_ids: set[int] | None = None) -> None:
    # Prefer the page title: it is the most stable mapping when other
    # Chromium/Electron windows are open on the desktop.
    hwnd = find_window(title_fragment)
    if hwnd is None:
        hwnd = find_window_for_processes(process_ids or set()) if process_ids else None
    if hwnd is None:
        foreground = win32gui.GetForegroundWindow()
        if foreground and "Chrome_WidgetWin" in win32gui.GetClassName(foreground):
            hwnd = foreground
        else:
            raise RuntimeError(f"Browser window not found: {title_fragment}")
    win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
    try:
        # Windows may keep another application (for example a game) in the
        # foreground. Attach the input queues briefly so the Edge window is
        # really activated before ImageGrab reads the screen rectangle.
        current_thread = ctypes.windll.kernel32.GetCurrentThreadId()
        target_thread, _ = win32process.GetWindowThreadProcessId(hwnd)
        foreground = win32gui.GetForegroundWindow()
        foreground_thread, _ = win32process.GetWindowThreadProcessId(foreground) if foreground else (0, 0)
        if foreground_thread and foreground_thread != current_thread:
            ctypes.windll.user32.AttachThreadInput(foreground_thread, current_thread, True)
        if target_thread != current_thread:
            ctypes.windll.user32.AttachThreadInput(target_thread, current_thread, True)
        ctypes.windll.user32.AllowSetForegroundWindow(-1)
        win32gui.BringWindowToTop(hwnd)
        win32gui.SetForegroundWindow(hwnd)
        win32gui.SetActiveWindow(hwnd)
        if target_thread != current_thread:
            ctypes.windll.user32.AttachThreadInput(target_thread, current_thread, False)
        if foreground_thread and foreground_thread != current_thread:
            ctypes.windll.user32.AttachThreadInput(foreground_thread, current_thread, False)
    except Exception:
        pass
    time.sleep(1.0)
    left, top, right, bottom = win32gui.GetWindowRect(hwnd)
    image = ImageGrab.grab(bbox=(left, top, right, bottom), include_layered_windows=True)
    image.save(path)


def wait(driver: webdriver.Edge, seconds: int = 15) -> WebDriverWait:
    return WebDriverWait(driver, seconds)


def first(driver: webdriver.Edge, selectors: list[tuple[str, str]]):
    for kind, value in selectors:
        try:
            return driver.find_element(getattr(By, kind), value)
        except NoSuchElementException:
            continue
    raise NoSuchElementException(str(selectors))


def screenshot_current(driver: webdriver.Edge, name: str, title_fragment: str | None = None) -> None:
    path = SCREENSHOTS / name
    driver.save_screenshot(str(path.with_name(path.stem + "_viewport.png")))
    capture_window(path, title_fragment or driver.title, browser_process_ids(driver))


def main() -> None:
    options = Options()
    options.accept_insecure_certs = True
    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")
    driver = webdriver.Edge(options=options)
    driver.set_page_load_timeout(30)
    try:
        # Assignment 1: full browser window, including address bar and port.
        driver.get("http://localhost:8088")
        wait(driver).until(EC.title_contains("Welcome to nginx"))
        screenshot_current(driver, "nginx_browser_full.png")

        # Portainer login and stack list.
        driver.get("https://localhost:9443")
        username = first(driver, [("NAME", "Username"), ("NAME", "username"), ("CSS_SELECTOR", "input[type='text']")])
        password = first(driver, [("NAME", "Password"), ("NAME", "password"), ("CSS_SELECTOR", "input[type='password']")])
        username.send_keys("admin")
        password.send_keys("PortainerLab-2026!")
        first(driver, [("CSS_SELECTOR", "button[type='submit']"), ("CSS_SELECTOR", "button")]).click()
        time.sleep(4)
        # The current Portainer UI requires selecting the Docker environment
        # before environment-specific routes such as the stack list resolve.
        wait(driver).until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'docker-desktop')]"))).click()
        time.sleep(2)
        driver.get("https://localhost:9443/#!/1/docker/stacks")
        time.sleep(4)
        screenshot_current(driver, "portainer_stack.png")
        driver.get("https://localhost:9443/#!/1/docker/containers")
        time.sleep(4)
        screenshot_current(driver, "portainer_nginx.png")
        # The container list itself is the evidence; keep the clean viewport
        # capture because another desktop window may cover the browser frame.
        driver.save_screenshot(str(SCREENSHOTS / "portainer_nginx.png"))

        # Grafana dashboard.
        driver.get("http://localhost:3000/login")
        time.sleep(2)
        wait(driver).until(EC.presence_of_element_located((By.NAME, "user")))
        user = first(driver, [("NAME", "user"), ("NAME", "username"), ("CSS_SELECTOR", "input[type='text']")])
        pwd = first(driver, [("NAME", "password"), ("CSS_SELECTOR", "input[type='password']")])
        user.send_keys("admin")
        pwd.send_keys("grafana-lab-2026")
        first(driver, [("CSS_SELECTOR", "button[type='submit']"), ("CSS_SELECTOR", "button")]).click()
        time.sleep(5)
        driver.get("http://localhost:3000/d/docker-observability-lab/docker-observability-lab")
        time.sleep(5)
        screenshot_current(driver, "grafana_dashboard.png")

        # VictoriaMetrics UI.
        driver.get("http://localhost:8428/vmui")
        time.sleep(4)
        screenshot_current(driver, "victoriametrics_status.png")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
