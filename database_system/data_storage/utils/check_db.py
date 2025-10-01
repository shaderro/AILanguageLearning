from sqlalchemy import create_engine, text
from ..config.config import DATABASE_CONFIG

def main(env: str = 'development'):
    engine = create_engine(DATABASE_CONFIG[env], echo=False, future=True)
    with engine.connect() as conn:
        for tbl in ['vocab_expressions','vocab_expression_examples','original_texts','sentences','tokens','grammar_rules','grammar_examples']:
            try:
                cnt = conn.execute(text(f"select count(*) from {tbl}")).scalar_one()
                print(f"{tbl}: {cnt}")
            except Exception:
                print(f"{tbl}: <no table>")

if __name__ == '__main__':
    main() 