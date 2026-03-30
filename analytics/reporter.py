import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler

logger = logging.getLogger(__name__)


class DailyReporter:
    def __init__(self, db_manager, telegram_sender):
        self.db = db_manager
        self.telegram = telegram_sender
        self.scheduler = BackgroundScheduler()

    def start(self):
        # Daily report at 8 PM
        self.scheduler.add_job(self.send_daily_report, "cron", hour=20, minute=0)
        # Weekly report on Sundays at 10 AM
        self.scheduler.add_job(self.send_weekly_report, "cron", day_of_week="sun", hour=10, minute=0)
        self.scheduler.start()
        logger.info("Reporter scheduler started (daily 8PM, weekly Sunday 10AM)")

    def stop(self):
        self.scheduler.shutdown(wait=False)

    def send_daily_report(self):
        try:
            today = datetime.utcnow().strftime("%Y-%m-%d")
            deals = self.db.get_daily_deals(today)

            if not deals:
                self.telegram.send_message(
                    "\U0001f4ca <b>Reporte Diario</b>\n\n"
                    "No se encontraron deals hoy.\n"
                    f"Fecha: {today}",
                    disable_notification=True,
                )
                return

            # Top 5 deals by score
            top_deals = deals[:5]
            total = len(deals)
            urgent = sum(1 for d in deals if d.get("alert_level") == "URGENT")
            high = sum(1 for d in deals if d.get("alert_level") == "HIGH")

            deal_lines = []
            for i, d in enumerate(top_deals, 1):
                price_str = f"${d['price_detected']:.2f}" if d.get("price_detected") else "N/A"
                deal_lines.append(
                    f"{i}. [{d.get('bot_score', 0)}pts] {d.get('title', '')[:60]}\n"
                    f"   r/{d.get('subreddit', '?')} | {price_str}"
                )

            text = (
                f"\U0001f4ca <b>Reporte Diario - {today}</b>\n"
                f"{'=' * 30}\n\n"
                f"\U0001f4e6 Total deals encontrados: {total}\n"
                f"\U0001f6a8 Urgentes: {urgent}\n"
                f"\U0001f525 Altos: {high}\n\n"
                f"<b>Top 5 Deals:</b>\n"
                f"{''.join(chr(10) + line for line in deal_lines)}"
            )

            self.telegram.send_message(text, disable_notification=True)

            # Update daily stats
            subreddit_counts = {}
            for d in deals:
                sub = d.get("subreddit", "unknown")
                subreddit_counts[sub] = subreddit_counts.get(sub, 0) + 1
            top_sub = max(subreddit_counts, key=subreddit_counts.get) if subreddit_counts else ""

            self.db.update_daily_stats({
                "total_posts_scanned": total,
                "total_alerts_sent": urgent + high,
                "urgent_alerts": urgent,
                "high_alerts": high,
                "top_subreddit": top_sub,
            })

        except Exception as e:
            logger.error("Daily report failed: %s", e)

    def send_weekly_report(self):
        try:
            stats = self.db.get_weekly_stats()
            hourly = self.db.get_hourly_distribution()

            # Best hours
            best_hours = ""
            if hourly:
                top3 = hourly[:3]
                best_hours = ", ".join(f"{h}:00 ({c} deals)" for h, c in top3)

            text = (
                f"\U0001f4c8 <b>Reporte Semanal</b>\n"
                f"{'=' * 30}\n\n"
                f"\U0001f4e6 Posts escaneados: {stats['total_scanned']}\n"
                f"\U0001f514 Alertas enviadas: {stats['total_alerted']}\n"
                f"\U0001f6a8 Alertas urgentes: {stats['urgent_count']}\n"
                f"\U0001f3c6 Top subreddit: r/{stats['top_subreddit']}\n"
            )

            if best_hours:
                text += f"\n\u23f0 <b>Mejores horas:</b> {best_hours}\n"

            self.telegram.send_message(text, disable_notification=True)

        except Exception as e:
            logger.error("Weekly report failed: %s", e)
