from app.routers.emergency_contacts import ensure_default_emergency_contacts

def run_startup_tasks():
    # apenas popula os contatos de emergência padrão (se ainda não existirem)
    ensure_default_emergency_contacts()
