from alembic import op
import sqlalchemy as sa

revision = '001_initial_migration'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        'restaurants',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('address', sa.String(length=200), nullable=True),
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('rating', sa.Integer(), nullable=True),
        sa.Column('tags', sa.String(length=200), nullable=True),
        sa.Column('image_url', sa.String(length=500), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_restaurants_id'), 'restaurants', ['id'], unique=False)
    op.create_index(op.f('ix_restaurants_name'), 'restaurants', ['name'], unique=False)
    
    op.create_table(
        'vote_records',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('restaurant_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.String(length=100), nullable=False),
        sa.Column('user_name', sa.String(length=100), nullable=True),
        sa.Column('vote_time', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_vote_records_id'), 'vote_records', ['id'], unique=False)
    
    op.create_table(
        'lottery_records',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('restaurant_id', sa.Integer(), nullable=False),
        sa.Column('winner_user_id', sa.String(length=100), nullable=True),
        sa.Column('winner_user_name', sa.String(length=100), nullable=True),
        sa.Column('lottery_time', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_lottery_records_id'), 'lottery_records', ['id'], unique=False)

def downgrade() -> None:
    op.drop_index(op.f('ix_lottery_records_id'), table_name='lottery_records')
    op.drop_table('lottery_records')
    op.drop_index(op.f('ix_vote_records_id'), table_name='vote_records')
    op.drop_table('vote_records')
    op.drop_index(op.f('ix_restaurants_name'), table_name='restaurants')
    op.drop_index(op.f('ix_restaurants_id'), table_name='restaurants')
    op.drop_table('restaurants')