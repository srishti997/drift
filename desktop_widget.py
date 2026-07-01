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


def clamp(value, minimum=0, maximum=100):
    try:
        value = float(value)
        return max(minimum, min(value, maximum))
    except Exception:
        return 0


class DriftWidget(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Drift")
        self.geometry("380x430")
        self.resizable(False, False)
        self.attributes("-topmost", True)

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.configure(fg_color="#070B12")

        self.container = ctk.CTkFrame(
            self,
            fg_color="#0D1423",
            corner_radius=24,
            border_width=1,
            border_color="#1E293B"
        )
        self.container.pack(fill="both", expand=True, padx=14, pady=14)

        self.header = ctk.CTkLabel(
            self.container,
            text="🧠 DRIFT",
            font=("Segoe UI", 28, "bold"),
            text_color="#22D3EE"
        )
        self.header.pack(pady=(22, 2))

        self.subtitle = ctk.CTkLabel(
            self.container,
            text="Human Observability Companion",
            font=("Segoe UI", 12),
            text_color="#64748B"
        )
        self.subtitle.pack(pady=(0, 18))

        self.score_label = ctk.CTkLabel(
            self.container,
            text="--",
            font=("Segoe UI", 54, "bold"),
            text_color="#F8FAFC"
        )
        self.score_label.pack()

        self.grade_label = ctk.CTkLabel(
            self.container,
            text="Grade --",
            font=("Segoe UI", 14, "bold"),
            text_color="#22D3EE"
        )
        self.grade_label.pack(pady=(0, 12))

        self.progress = ctk.CTkProgressBar(
            self.container,
            width=260,
            height=10,
            corner_radius=10,
            progress_color="#22D3EE",
            fg_color="#1E293B"
        )
        self.progress.pack(pady=(0, 20))
        self.progress.set(0)

        self.info_frame = ctk.CTkFrame(
            self.container,
            fg_color="#111827",
            corner_radius=18
        )
        self.info_frame.pack(fill="x", padx=20, pady=(0, 16))

        self.mission_label = ctk.CTkLabel(
            self.info_frame,
            text="Mission: --",
            font=("Segoe UI", 14, "bold"),
            text_color="#E2E8F0",
            wraplength=300,
            justify="center"
        )
        self.mission_label.pack(pady=(16, 6))

        self.deep_work_label = ctk.CTkLabel(
            self.info_frame,
            text="Deep Work: --",
            font=("Segoe UI", 13),
            text_color="#94A3B8"
        )
        self.deep_work_label.pack(pady=4)

        self.risk_label = ctk.CTkLabel(
            self.info_frame,
            text="Risk: --",
            font=("Segoe UI", 13, "bold"),
            text_color="#34D399"
        )
        self.risk_label.pack(pady=(4, 16))

        self.insight_frame = ctk.CTkFrame(
            self.container,
            fg_color="#061826",
            corner_radius=18,
            border_width=1,
            border_color="#0E7490"
        )
        self.insight_frame.pack(fill="x", padx=20, pady=(0, 18))

        self.insight_title = ctk.CTkLabel(
            self.insight_frame,
            text="AI INSIGHT",
            font=("Segoe UI", 10, "bold"),
            text_color="#22D3EE"
        )
        self.insight_title.pack(pady=(12, 4))

        self.insight_label = ctk.CTkLabel(
            self.insight_frame,
            text="Collecting behavior signals...",
            font=("Segoe UI", 12),
            text_color="#CBD5E1",
            wraplength=300,
            justify="center"
        )
        self.insight_label.pack(padx=16, pady=(0, 14))

        self.footer = ctk.CTkLabel(
            self.container,
            text="Updates every 10 seconds",
            font=("Segoe UI", 10),
            text_color="#334155"
        )
        self.footer.pack(pady=(0, 12))

        self.refresh_data()

    def refresh_data(self):
        score = get_data("/score") or {}
        report = get_data("/daily-report") or {}
        deep_work = get_data("/deep-work") or {}
        prediction = get_data("/predict") or {}
        autopsy = get_data("/autopsy") or {}

        overall = clamp(score.get("overall_score", 0))
        grade = score.get("grade", "--")

        self.score_label.configure(text=f"{overall:.0f}")
        self.grade_label.configure(text=f"Grade {grade}")
        self.progress.set(overall / 100)

        if overall >= 75:
            color = "#34D399"
        elif overall >= 50:
            color = "#FBBF24"
        else:
            color = "#F87171"

        self.score_label.configure(text_color=color)
        self.progress.configure(progress_color=color)

        mission = report.get("top_mission", "--")
        self.mission_label.configure(text=f"Mission: {mission}")

        deep_minutes = deep_work.get("total_deep_work_minutes", "--")
        self.deep_work_label.configure(text=f"Deep Work: {deep_minutes} min")

        risk = prediction.get("risk_level", prediction.get("risk", "--"))

        risk_color = {
            "LOW": "#34D399",
            "MEDIUM": "#FBBF24",
            "HIGH": "#FB923C",
            "CRITICAL": "#F87171",
        }.get(str(risk).upper(), "#94A3B8")

        self.risk_label.configure(text=f"Risk: {risk}", text_color=risk_color)

        insight = autopsy.get("recommendation") or score.get("summary") or "Tracking your current work pattern."
        self.insight_label.configure(text=insight)

        self.after(10000, self.refresh_data)


if __name__ == "__main__":
    app = DriftWidget()
    app.mainloop()