from pathlib import Path
from typing import List

import click
from langchain_community.llms.ollama import Ollama
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables.base import RunnableSequence
from progress.bar import Bar
from pyfs import resolvePath

SYSTEM_PROMPT: str = """This file contains code for counting lines of code of software projects.
Generate suitable docstring for these Python functions in Google's style.
Do not explain the result.
Return as raw text"""


def readFile(path: Path) -> str:
    with open(file=path, mode="r") as sourceFile:
        code: List[str] = sourceFile.readlines()
        sourceFile.close()

    return "".join(code)


def segmentFunctions(code: str) -> List[str]:
    return [c.strip() for c in code.split(sep="def ")[1:]]


def inference(systemPrompt: str, code: str, model: str = "codegemma") -> str:
    output_parser = StrOutputParser()
    chatPrompt: ChatPromptTemplate = ChatPromptTemplate.from_messages(
        [("system", systemPrompt), ("user", "{input}")]
    )

    llm: Ollama = Ollama(model=model)

    chain: RunnableSequence = chatPrompt | llm | output_parser

    return chain.invoke({"input": code})


@click.command()
@click.option(
    "-s",
    "--system",
    "systemPrompt",
    type=str,
    required=False,
    default=SYSTEM_PROMPT,
    help="System prompt",
)
@click.option(
    "-i",
    "--input",
    "sourceFile",
    type=Path,
    required=True,
    help="File to analyze",
)
@click.option(
    "-o",
    "--output",
    "output",
    type=Path,
    required=True,
    help="File to output to",
)
def main(systemPrompt: str, sourceFile: Path, output: Path) -> None:
    data: List[str] = []
    sf: Path = resolvePath(path=sourceFile)

    code: str = readFile(path=sf)
    functions: List[str] = segmentFunctions(code=code)

    with Bar("Generating docstrings...", max=len(functions)) as bar:
        func: str
        for func in functions:
            data.append(inference(systemPrompt=systemPrompt, code=func))
            bar.next()

    with open(file=output, mode="w") as outputFile:
        code: str
        for code in data:
            outputFile.write(code + "\n\n---\n\n")
        outputFile.close()


if __name__ == "__main__":
    main()
