import click

# nuitka-skip-unless-imports: click

@click.command()
@click.option("--count", default=3, help="Number of greetings.")
@click.option("--fname", prompt="Your first name", help="First name of the person to greet.")
@click.option("--sname", prompt="Your second name", help="Second name of the person to greet.")

def hello(count, fname, sname):
        """Simple program that greets NAME for a total of COUNT times."""
        for _ in range(count):
                click.echo("Hello, %s %s!" % (fname, sname))

def main(*args):
        hello(*args)


if __name__ == '__main__':
        commands = '--count=7 --fname=Tabi --sname=Derick'

