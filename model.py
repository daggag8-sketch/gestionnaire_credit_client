from flask_login import UserMixin
from datetime import datetime
from .extensions import db
from flask_wtf import FlaskForm
from wtforms import StringField,SubmitField,EmailField
from wtforms.validators import Optional,Email

class Client(db.Model):
    __tablename__ = "client"

    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(20),nullable=False)
    prenom = db.Column(db.String(80),nullable=False)
    telephone = db.Column(db.String(20),nullable=False)
    adresse = db.Column(db.String(255),nullable=False)
    create_at= db.Column(db.DateTime,default=datetime.utcnow,nullable=False)
    credit = db.relationship("Credit", back_populates="client")

class Article(db.Model):
    __tablename__ = "article"

    id = db.Column(db.Integer, primary_key=True)
    nom_art = db.Column(db.String(20),nullable=False)
    prix_unitaire = db.Column(db.Numeric(10, 2), nullable=False)
    stock = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(255), nullable=False)
    details = db.relationship("Detail_credit", back_populates="article_rel")

class Credit(db.Model):
    __tablename__ = "credit"

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False,default=datetime.utcnow)
    montant_total = db.Column(db.Numeric(10,2),nullable=False)
    statut = db.Column(db.String(255), nullable=False)
    id_client = db.Column(db.Integer, db.ForeignKey('client.id'),nullable=False)
    client = db.relationship("Client", back_populates="credit")
    details = db.relationship("Detail_credit", back_populates="credit_rel")

class Detail_credit(db.Model):
    __tablename__ = "detail_credit"

    id = db.Column(db.Integer, primary_key=True)
    quantite = db.Column(db.Integer, nullable=False)
    prix_unitaire = db.Column(db.Numeric(10, 2), nullable=False)
    montant = db.Column(db.Numeric(10, 2), nullable=False)
    date = db.Column(db.DateTime, nullable=False,default=datetime.utcnow)
    montant_payer = db.Column(db.Numeric(10,2),nullable=False)
    rest_a_payer = db.Column(db.Numeric(10,2),nullable=False)
    credit = db.Column(db.Integer,db.ForeignKey('credit.id'),nullable=False)
    article = db.Column(db.Integer,db.ForeignKey('article.id'),nullable=False)
    credit_rel = db.relationship("Credit", back_populates="details")
    article_rel = db.relationship("Article", back_populates="details")


class Utilisateur(UserMixin, db.Model):
    __tablename__ = "utilisateur"
    id = db.Column(db.Integer, primary_key=True)
    nom_user = db.Column(db.String(100), nullable=False)
    mot_de_passe = db.Column(db.String(255), nullable=False)
    telephone = db.Column(db.String(20), nullable=False)
    role = db.Column(db.String(80), nullable=False)


class Vente(db.Model):
    __tablename__ = "vente"

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, default=datetime.utcnow)

    id_client = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    client = db.relationship("Client")

    montant_total = db.Column(db.Numeric(10,2), nullable=False)
    montant_paye = db.Column(db.Numeric(10,2), default=0)
    reste = db.Column(db.Numeric(10,2), nullable=False)

    statut = db.Column(db.String(20), nullable=False)  # complet / precompte / credit
    id_credit = db.Column(db.Integer, db.ForeignKey('credit.id'), nullable=True)
    credit_rel = db.relationship("Credit")
    paiements = db.relationship("Paiement", back_populates="vente", order_by="Paiement.date")

class LigneVente(db.Model):
    __tablename__ = "ligne_vente"

    id = db.Column(db.Integer, primary_key=True)

    id_vente = db.Column(db.Integer, db.ForeignKey('vente.id'))
    id_article = db.Column(db.Integer, db.ForeignKey('article.id'))

    quantite = db.Column(db.Integer, nullable=False)
    prix_unitaire = db.Column(db.Numeric(10,2), nullable=False)
    montant = db.Column(db.Numeric(10,2), nullable=False)

    vente = db.relationship("Vente", backref="lignes")
    article = db.relationship("Article")


class Paiement(db.Model):
    __tablename__ = "paiement"

    id = db.Column(db.Integer, primary_key=True)
    id_vente = db.Column(db.Integer, db.ForeignKey('vente.id'), nullable=False)
    montant = db.Column(db.Numeric(10, 2), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    vente = db.relationship("Vente", back_populates="paiements")



    


