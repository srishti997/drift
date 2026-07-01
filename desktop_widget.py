import requests
import customtkinter as ctk

API_BASE_URL = "http://127.0.0.1:8000"


def get_data(endpoint):
    try:
        response = requests.get(f"{API_BASE_URL}{endpoint}", timeout=3)
        response.raise_for_status()
        return response.json()
    except Exception:
        return None


class DriftWidget(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Drift")
        self.geometry("320x260")
        self.attributes("-topmost", True)

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title_label = ctk.CTkLabel(
            self,
            text="🧠 Drift",
            font=("Arial", 28, "bold")
        )
        self.title_label.pack(pady=(20, 5))

        self.subtitle = ctk.CTkLabel(
            self,
            text="Human Observability",
            font=("Arial", 12)
        )
        self.subtitle.pack(pady=(0, 20))

        self.score_label = ctk.CTkLabel(self, text="Score: --", font=("Arial", 20))
        self.score_label.pack(pady=5)

        self.mission_label = ctk.CTkLabel(self, text="Mission: --", font=("Arial", 15))
        self.mission_label.pack(pady=5)

        self.deep_work_label = ctk.CTkLabel(self, text="Deep Work: --", font=("Arial", 15))
        self.deep_work_label.pack(pady=5)

        self.risk_label = ctk.CTkLabel(self, text="Risk: --", font=("Arial", 15))
        self.risk_label.pack(pady=5)

        self.refresh_data()

    def refresh_data(self):
        score = get_data("/score") or {}
        report = get_data("/daily-report") or {}
        deep_work = get_data("/deep-work") or {}
        prediction = get_data("/predict") or {}

        self.score_label.configure(
            text=f"Score: {score.get('overall_score', '--')} | Grade: {score.get('grade', '--')}"
        )

        self.mission_label.configure(
            text=f"Mission: {report.get('top_mission', '--')}"
        )

        self.deep_work_label.configure(
            text=f"Deep Work: {deep_work.get('total_deep_work_minutes', '--')} min"
        )

        risk = prediction.get("risk_level", prediction.get("risk", "--"))

        self.risk_label.configure(
            text=f"Risk: {risk}"
        )

        self.after(10000, self.refresh_data)


if __name__ == "__main__":
    app = DriftWidget()
    app.mainloop()