import json
import os
from datetime import datetime, timedelta


class TimeRecord:
    def __init__(self, start_time, end_time, category="Study"):
        self.start_time = start_time  # datetime object
        self.end_time = end_time  # datetime object
        self.category = category

    def to_dict(self):
        return {
            "start": self.start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "end": self.end_time.strftime("%Y-%m-%d %H:%M:%S"),
            "category": self.category
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            datetime.strptime(data["start"], "%Y-%m-%d %H:%M:%S"),
            datetime.strptime(data["end"], "%Y-%m-%d %H:%M:%S"),
            data.get("category", "Study")
        )


class DataManager:
    VERSION = "1.1.0"

    def __init__(self, storage_path="records.json"):
        self.storage_path = storage_path
        self.records = []
        self.settings = {
            "wallpaper": "",
            "wallpaper_opacity": 1.0,
            "slogan": "保持专注，更进一步",
            "show_slogan": True,
            "tags": ["Study", "Game", "Rest", "Work"],
            "version": self.VERSION
        }
        self.load_data()

    def add_record(self, start_dt, end_dt, category="Study"):
        """处理跨天记录并支持标签"""
        current_dt = start_dt
        while current_dt.date() < end_dt.date():
            # 记录到当天午夜
            midnight = datetime.combine(current_dt.date() + timedelta(days=1), datetime.min.time())
            self.records.append(TimeRecord(current_dt, midnight, category))
            current_dt = midnight

        # 记录最后一段
        self.records.append(TimeRecord(current_dt, end_dt, category))
        self.save_data()

    def load_data(self):
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.records = [TimeRecord.from_dict(r) for r in data.get("records", [])]
                    # 合并设置，确保新功能（如 tags）有默认值
                    saved_settings = data.get("settings", {})
                    for key, value in saved_settings.items():
                        self.settings[key] = value

                    # 确保 tags 始终存在
                    if "tags" not in self.settings:
                        self.settings["tags"] = ["Study", "Game", "Rest", "Work"]

            except Exception as e:
                print(f"Error loading data: {e}")

    def save_data(self):
        data = {
            "records": [r.to_dict() for r in self.records],
            "settings": self.settings,
            "version": self.VERSION
        }
        with open(self.storage_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def export_data(self, path):
        self.save_data()
        import shutil
        shutil.copy(self.storage_path, path)

    def import_data(self, path):
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                new_data = json.load(f)
                new_records = [TimeRecord.from_dict(r) for r in new_data.get("records", [])]
                self.records.extend(new_records)

                # 合并标签
                new_tags = new_data.get("settings", {}).get("tags", [])
                for tag in new_tags:
                    if tag not in self.settings["tags"]:
                        self.settings["tags"].append(tag)

                self.save_data()
                return True
        return False