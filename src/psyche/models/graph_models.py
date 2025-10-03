from psyche.models.base import Base
from sqlalchemy import Integer, String, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

class Graph(Base):
  __tablename__ = "graph"

  id: Mapped[int] = mapped_column(Integer, primary_key=True)
  data: Mapped[dict] = mapped_column(JSON)

class Node(Base):
  __tablename__ = "node"

  id: Mapped[int] = mapped_column(Integer, primary_key=True)
  graph_id: Mapped[int] = mapped_column(
      Integer, ForeignKey("graph.id", ondelete="CASCADE"))
  data: Mapped[dict] = mapped_column(JSON)

class Edge(Base):
  __tablename__ = "edge"

  id: Mapped[int] = mapped_column(Integer, primary_key=True)
  graph_id: Mapped[int] = mapped_column(Integer)
  source_node_id: Mapped[int] = mapped_column(
      Integer, ForeignKey("node.id", ondelete="CASCADE"))
  target_node_id: Mapped[int] = mapped_column(
      Integer, ForeignKey("node.id", ondelete="CASCADE"))
  is_directed: Mapped[bool] = mapped_column(default=True)
  data: Mapped[dict] = mapped_column(JSON)
