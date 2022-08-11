# discord-sales-bot

## Note

Due to Opensea's API changes on 08/03/2022, pagination is performed with a cursor. For that reason, if the sales bot ever goes down, to simplify the design, only the last trade will be looked at. From that point onwards, all of the trades will be watched for.

## Dev

Prepare environment. You will need to install [poetry](https://python-poetry.org/).

To install dependencies

```bash
poetry install
```

Then, drop into the virtual environemnt you have just created

```bash
poetry shell
```

Now, set up the `pre-commit` to adhere to the code style

```bash
pre-commit install
```

You are ready to develop and run the script

You can activate the poetry env by running

`~/.pyenv/shims/python3.9 -m poetry shell`
