"""Add processos_dje table"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '003'
down_revision = '002'

def upgrade():
    op.create_table(
        'processos_dje',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('numero', sa.String(), nullable=False),
        sa.Column('tipo', sa.String()),
        sa.Column('classe', sa.String()),
        sa.Column('comarca', sa.String()),
        sa.Column('codigo_comarca', sa.String()),
        sa.Column('partes', postgresql.JSON(astext_type=sa.Text())),
        sa.Column('advogados', postgresql.JSON(astext_type=sa.Text())),
        sa.Column('valor_causa', sa.String()),
        sa.Column('data_dje', sa.String()),
        sa.Column('caderno', sa.String()),
        sa.Column('pagina_dje', sa.Integer()),
        sa.Column('created_at', sa.DateTime()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_processos_dje_numero', 'processos_dje', ['numero'], unique=True)
    op.create_index('ix_processos_dje_tipo', 'processos_dje', ['tipo'])
    op.create_index('ix_processos_dje_comarca', 'processos_dje', ['comarca'])

def downgrade():
    op.drop_table('processos_dje')
