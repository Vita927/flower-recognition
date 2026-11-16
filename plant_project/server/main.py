"""Консольное приложение сервера распознавания растений.

Запуск сервера:      python main.py serve --port 8000
Проверка без сети:   python main.py predict photo.jpg --top-k 3
"""
import argparse
import socket


def lan_ip() -> str:
    """IP компьютера в локальной сети (его нужно вводить в приложении на телефоне)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()


def cmd_serve(args: argparse.Namespace) -> None:
    import uvicorn

    from app.api import app, classes, model

    print("=" * 60)
    print(f" Plant API запущен. Модель: {model.version}, классов: {len(classes)}")
    print(f" Для эмулятора Android:  http://10.0.2.2:{args.port}")
    print(f" Для реального телефона: http://{lan_ip()}:{args.port}")
    print(f" Документация (Swagger): http://localhost:{args.port}/docs")
    print("=" * 60)
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


def cmd_predict(args: argparse.Namespace) -> None:
    from PIL import Image

    from app.api import classes, model

    image = Image.open(args.image).convert("RGB")
    for cid, prob in model.predict(image, args.top_k):
        print(f"{prob:6.1%}  {classes[cid].name_ru} ({classes[cid].label})")


def main() -> None:
    parser = argparse.ArgumentParser(description="Plant recognition server")
    sub = parser.add_subparsers(dest="command")

    serve = sub.add_parser("serve", help="запустить HTTP-сервер")
    serve.add_argument("--host", default="0.0.0.0", help="0.0.0.0 = виден телефону в сети")
    serve.add_argument("--port", type=int, default=8000)
    serve.set_defaults(func=cmd_serve)

    pred = sub.add_parser("predict", help="распознать файл локально")
    pred.add_argument("image")
    pred.add_argument("--top-k", type=int, default=5)
    pred.set_defaults(func=cmd_predict)

    args = parser.parse_args()
    if not hasattr(args, "func"):
        args = parser.parse_args(["serve"])
    args.func(args)


if __name__ == "__main__":
    main()
