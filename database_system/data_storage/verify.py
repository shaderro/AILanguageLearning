from sqlalchemy import create_engine, text
from .config.config import DATABASE_CONFIG

def main(env: str = 'development'):
    engine = create_engine(DATABASE_CONFIG[env], echo=False, future=True)
    with engine.connect() as conn:
        def count(tbl):
            try:
                return conn.execute(text(f"select count(*) from {tbl}")).scalar_one()
            except Exception:
                return None
        vocab = count('vocab_expressions')
        examples = count('vocab_expression_examples')
        print(f"vocab_expressions={vocab}, vocab_expression_examples={examples}")
        try:
            joined = conn.execute(text(
                """
                select count(distinct v.vocab_id)
                from vocab_expressions v
                join vocab_expression_examples e on v.vocab_id = e.vocab_id
                """
            )).scalar_one()
            print(f"vocab_with_examples={joined}")
        except Exception:
            print("vocab_with_examples=<not available>")

if __name__ == '__main__':
    main() 