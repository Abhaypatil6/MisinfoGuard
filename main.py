import argparse
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from src.agents.monitor import MonitorAgent
from src.agents.verifier import VerifierAgent
from src.agents.explainer import ExplainerAgent

console = Console()

def main():
    parser = argparse.ArgumentParser(description="MisinfoGuard: AI Agent for Misinformation Detection")
    parser.add_argument("--topic", type=str, required=True, help="Topic to scan for misinformation (e.g., 'Climate Change')")
    args = parser.parse_args()

    console.print(Panel(f"[bold blue]MisinfoGuard Activated[/bold blue]\nScanning topic: [bold]{args.topic}[/bold]"))

    # 1. Monitor
    monitor = MonitorAgent()
    console.print("[bold green]Scanning for claims...[/bold green]")
    claims = monitor.scan(args.topic)
    
    if not claims:
        console.print("[red]No claims found.[/red]")
        return

    console.print(f"[bold]Identified {len(claims)} potential claims.[/bold]")
    for i, claim in enumerate(claims, 1):
        console.print(f"{i}. {claim}")

    # 2. Verify & Explain (Process the first 2 claims for demo purposes)
    verifier = VerifierAgent()
    explainer = ExplainerAgent()

    for claim in claims[:2]: 
        console.print(Panel(f"[bold yellow]Processing Claim:[/bold yellow] {claim}"))
        
        # Verify
        console.print("[bold cyan]Verifying...[/bold cyan]")
        verification_result = verifier.verify(claim)
        
        status_color = "green" if verification_result.get("status") == "True" else "red"
        console.print(f"Status: [{status_color}]{verification_result.get('status')}[/{status_color}]")
        
        # Explain
        console.print("[bold magenta]Generating explanation...[/bold magenta]")
        explanation = explainer.explain(claim, verification_result)
        
        console.print(Markdown(explanation))
        console.print("-" * 40)

if __name__ == "__main__":
    main()
