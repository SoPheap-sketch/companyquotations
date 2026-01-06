from app.models import Project, Quote

def get_dashboard_data(db):
    total_projects = db.query(Project).count()

    pending_estimates = (
        db.query(Quote)
        .filter(Quote.status.in_(["draft", "pending"]))
        .count()
    )

    approved_quotes = (
        db.query(Quote)
        .filter(Quote.status == "approved")
        .count()
    )

    recent_projects = (
        db.query(Project)
        .order_by(Project.id.desc())
        .limit(5)
        .all()
    )

    recent_quotes = (
        db.query(Quote)
        .order_by(Quote.id.desc())
        .limit(5)
        .all()
    )

    return {
        "total_projects": total_projects,
        "pending_estimates": pending_estimates,
        "approved_quotes": approved_quotes,
        "recent_projects": recent_projects,
        "recent_quotes": recent_quotes,
    }
