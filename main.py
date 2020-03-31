import logging

from argparse import ArgumentParser
from pnpbot.bot import PnPBot

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.WARN,
        format="%(asctime)s - %(levelname)s [%(filename)s]: %(message)s",
    )
    _logger = logging.getLogger("pnpbot")
    _logger.setLevel(logging.DEBUG)
    parser = ArgumentParser()
    parser.add_argument("--token", required=True)
    parser.add_argument("--channel", type=int, required=True)
    parser.add_argument("--system", required=True)

    args = parser.parse_args()

    _logger.info("Starting up bot ...")
    bot = PnPBot(args.system, args.channel)
    bot.run(args.token)
