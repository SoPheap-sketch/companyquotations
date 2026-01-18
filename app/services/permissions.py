def has_permission(user_role: str, action: str) -> bool:
    permissions = {
        "admin": [
            "create_project", "edit_project", "delete_project",
            "create_quote", "edit_quote", "submit_quote", "approve_quote",
            "view_pdf", "manage_users"
        ],
        "ceo": ["approve_quote", "view_pdf"],
        "manager": ["create_project", "edit_project", "create_quote", "submit_quote"],
        "architect": ["create_quote", "edit_quote"],
        "designer": ["edit_quote"],
        "interpreter": []
    }

    return action in permissions.get(user_role, [])
