#!/usr/bin/env python3
"""Debug version of agent worker with more output."""

import asyncio
import os
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env", override=True)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.kanban.models import Base, TicketStatus
from src.kanban.crud_async import TicketCRUD, CommentCRUD
from src.kanban.schemas import TicketUpdate
from src.git_provider import GitHubProvider
from src.llm import KimiClient
from src.agents import DeveloperAgent

DATABASE_URL = "sqlite:///./kanban.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

async def main():
    print("=" * 60)
    print("🤖 DEBUG Agent Worker")
    print("=" * 60)
    
    db = SessionLocal()
    ticket_crud = TicketCRUD(db)
    comment_crud = CommentCRUD(db)
    
    github_token = os.getenv("GITHUB_TOKEN")
    router_key = os.getenv("OPEN_ROUTER_API_KEY") or os.getenv("OPENROUTER_API_KEY")
    
    print(f"GitHub token: {'✓' if github_token else '✗'}")
    print(f"Router key: {'✓' if router_key else '✗'}")
    
    git_provider = GitHubProvider(github_token)
    llm_client = KimiClient()
    
    agent = DeveloperAgent(
        agent_id="mohami",
        git_provider=git_provider,
        llm_client=llm_client,
        ticket_crud=ticket_crud,
        comment_crud=comment_crud
    )
    
    print(f"\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Starting...")
    
    while True:
        try:
            print(f"\n--- Poll at {datetime.now().strftime('%H:%M:%S')} ---")
            
            # Check backlog
            open_tickets = await ticket_crud.list(
                status=TicketStatus.BACKLOG,
                agent=None
            )
            print(f"Backlog tickets: {len(open_tickets)}")
            
            for ticket in open_tickets:
                print(f"  Processing new ticket: {ticket.id}")
                await agent.process_ticket(ticket.id)
            
            # Check clarification
            clarification_tickets = await ticket_crud.list(
                status=TicketStatus.CLARIFICATION
            )
            print(f"Clarification tickets: {len(clarification_tickets)}")
            
            for ticket in clarification_tickets:
                print(f"  Ticket {ticket.id}: agent={ticket.agent}")
                if ticket.agent == "mohami":
                    comments = await comment_crud.get_by_ticket(ticket.id)
                    print(f"    Comments: {len(comments)}")
                    
                    if comments:
                        latest = comments[0]
                        print(f"    Latest: {latest.author} at {latest.created_at}")
                        print(f"    Is mohami: {latest.author.startswith('mohami')}")
                        
                        if not latest.author.startswith("mohami"):
                            print(f"    -> PROCESSING!")
                            await agent.process_ticket(ticket.id)
                        else:
                            print(f"    -> Waiting for user response")
                else:
                    print(f"    -> Not assigned to mohami")
                    
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()
        
        await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())
