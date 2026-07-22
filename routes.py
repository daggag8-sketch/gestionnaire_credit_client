from flask import Blueprint,render_template,request,flash,redirect,url_for
from .model import Client, Article, Vente, LigneVente, Credit, Detail_credit, Utilisateur, Paiement
from .extensions import db
from werkzeug.security import generate_password_hash,check_password_hash
from flask_login import login_user, login_required, logout_user, current_user
from sqlalchemy import func, extract
from datetime import datetime,timedelta
 


routes = Blueprint("routes",__name__)

# 🔐 LOGIN
@routes.route('/', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('routes.dashboard'))

    if request.method == 'POST':
        telephone = request.form.get('telephone')
        mot_de_passe = request.form.get('mot_de_passe')

        # ✅ Vérification champs vides
        if not telephone or not mot_de_passe:
            flash("Veuillez remplir tous les champs ❗", "error")
            return redirect(url_for('routes.login'))

        user = Utilisateur.query.filter_by(telephone=telephone).first()

        # ✅ Vérification sécurisée
        if user and check_password_hash(user.mot_de_passe, mot_de_passe):
            login_user(user)

            flash("Connexion réussie ✅", "success")
            return redirect(url_for('routes.dashboard'))
        else:
            flash("Numéro ou mot de passe incorrect ❌", "error")

    return render_template("login.html")


# 🚪 LOGOUT
@routes.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Déconnexion réussie 👋", "success")
    return redirect(url_for('routes.login'))


# 🔥 DASHBOARD
@routes.route('/dashboard')
@login_required
def dashboard():

    # 📊 STATISTIQUES GLOBALES (hors ventes annulées)
    total_clients = Client.query.count()
    total_articles = Article.query.count()
    total_ventes = Vente.query.filter(Vente.statut != 'annulee').count()
    total_credits = Credit.query.filter(Credit.statut != 'annulee').count()

    # 💰 CHIFFRES GLOBAUX (hors ventes annulées)
    total_chiffre = db.session.query(func.sum(Vente.montant_total)).filter(
        Vente.statut != 'annulee'
    ).scalar() or 0

    total_paiements = db.session.query(func.sum(Vente.montant_paye)).filter(
        Vente.statut != 'annulee'
    ).scalar() or 0

    total_reste_credit = db.session.query(func.sum(Vente.reste)).filter(
        Vente.statut.in_(["credit", "precompte"])
    ).scalar() or 0

    total_prix_articles = db.session.query(
        func.sum(Article.prix_unitaire * Article.stock)
    ).scalar() or 0

    total_montant_ventes = total_chiffre

    # 📅 LABELS DES 6 DERNIERS MOIS
    mois_noms = ["Jan","Fév","Mars","Avr","Mai","Juin",
                 "Juil","Aoû","Sep","Oct","Nov","Déc"]

    mois_actuel = datetime.now().month
    mois_indices = [((mois_actuel - i - 1) % 12) + 1 for i in range(5, -1, -1)]
    labels = [mois_noms[m - 1] for m in mois_indices]

    # 📊 MONTANT ENCAISSÉ PAR MOIS (hors ventes annulées)
    data = []
    for m in mois_indices:
        montant = db.session.query(func.sum(Vente.montant_paye)).filter(
            extract('month', Vente.date) == m,
            Vente.statut != 'annulee'
        ).scalar() or 0
        data.append(float(montant))

    # 📊 MONTANT EN CREDIT PAR MOIS (hors ventes annulées)
    data_credits = []
    for m in mois_indices:
        montant = db.session.query(func.sum(Vente.reste)).filter(
            extract('month', Vente.date) == m,
            Vente.statut.in_(["credit", "precompte"])
        ).scalar() or 0
        data_credits.append(float(montant))

    # 🔥 VENTES RECENTES (tableau historique, hors annulées)
    ventes_recentes = Vente.query.filter(
        Vente.statut != 'annulee'
    ).order_by(Vente.id.desc()).limit(5).all()

    return render_template(
        "dashboard.html",
        total_clients=total_clients,
        total_articles=total_articles,
        total_ventes=total_ventes,
        total_credits=total_credits,
        total_chiffre=total_chiffre,
        total_paiements=total_paiements,
        total_reste_credit=total_reste_credit,
        total_prix_articles=total_prix_articles,
        total_montant_ventes=total_montant_ventes,
        labels=labels,
        data=data,
        data_credits=data_credits,
        ventes_recentes=ventes_recentes
    )

# ================= PARAMETRES =================
@routes.route('/parametre', methods=['GET', 'POST'])
@login_required
def parametre():

    if request.method == 'POST':
        nouveau_nom = request.form.get('nom_user')
        nouveau_telephone = request.form.get('telephone')
        ancien_mdp = request.form.get('ancien_mot_de_passe')
        nouveau_mdp = request.form.get('nouveau_mot_de_passe')

        current_user.nom_user = nouveau_nom
        current_user.telephone = nouveau_telephone

        # ✅ Changement de mot de passe seulement si rempli
        if ancien_mdp and nouveau_mdp:
            if check_password_hash(current_user.mot_de_passe, ancien_mdp):
                current_user.mot_de_passe = generate_password_hash(nouveau_mdp)
                flash("Profil et mot de passe mis à jour ✅", "success")
            else:
                flash("Ancien mot de passe incorrect ❌", "error")
                return redirect(url_for('routes.parametre'))
        else:
            flash("Profil mis à jour ✅", "success")

        db.session.commit()
        return redirect(url_for('routes.parametre'))

    return render_template("parametre.html")

# ================= CLIENT =================
@routes.route('/addclient', methods=['GET','POST'])
@login_required
def addclient():
    if request.method == 'POST':
        nom = request.form.get('nom')
        prenom = request.form.get('prenom')
        telephone = request.form.get('telephone')
        adresse = request.form.get('adresse')

        new_client = Client(nom=nom, prenom=prenom, telephone=telephone, adresse=adresse)
        db.session.add(new_client)
        db.session.commit()

        flash("Client ajouté !", "success")
        return redirect(url_for('routes.client'))

    return render_template("addclient.html")


@routes.route('/client')
@login_required
def client():
    clients = Client.query.all()

    credits_en_cours = {}
    for c in clients:
        total_reste = db.session.query(func.sum(Vente.reste)).filter(
            Vente.id_client == c.id,
            Vente.statut.in_(['credit', 'precompte'])
        ).scalar() or 0
        credits_en_cours[c.id] = float(total_reste)

    return render_template("client.html", clients=clients, credits_en_cours=credits_en_cours)

@routes.route('/modifclientAffichage')
@login_required
def modifclientAffiche():
    clients = Client.query.all()
    return render_template("modifclientAffiche.html", clients=clients)


# ✅ correction route
@routes.route('/modifclient/<int:id>', methods=['POST'])
@login_required
def modifclient(id):
    client = Client.query.get_or_404(id)

    client.nom = request.form.get('nom')
    client.prenom = request.form.get('prenom')
    client.telephone = request.form.get('telephone')
    client.adresse = request.form.get('adresse')

    db.session.commit()
    flash("Client modifié !", "success")
    return redirect(url_for('routes.modifclientAffiche'))


# ✅ correction route
@routes.route('/modifclient/<int:id>', methods=['GET'])
@login_required
def show_update_form(id):
    client = Client.query.get_or_404(id)
    return render_template('modifclient.html', client=client)

@routes.route('/client/<int:id>/historique')
@login_required
def historique_client(id):
    client = Client.query.get_or_404(id)

    ventes = Vente.query.filter_by(id_client=id).order_by(Vente.date.desc()).all()

    total_reste = sum(
        float(v.reste) for v in ventes if v.statut in ['credit', 'precompte']
    )
    total_achete = sum(float(v.montant_total) for v in ventes)
    total_paye = sum(float(v.montant_paye) for v in ventes)

    return render_template(
        "historique_client.html",
        client=client,
        ventes=ventes,
        total_reste=total_reste,
        total_achete=total_achete,
        total_paye=total_paye
    )


# 🔹 SUPPRESSION CLIENT
@routes.route('/supprimclientAffichage')
@login_required
def supprimclientAffiche():
    clients = Client.query.all()
    return render_template("supprimclientAffiche.html", clients=clients)


# ✅ correction route + indentation try
@routes.route('/supprimclient/<int:id>')
@login_required
def supprimclient(id):
    client = Client.query.get_or_404(id)

    try:
        db.session.delete(client)
        db.session.commit()
        flash("Client supprimé !", "success")
    except:
        flash("Erreur suppression", "error")

    return redirect(url_for('routes.supprimclientAffiche'))

# ================= ARTICLE =================
@routes.route('/addarticle', methods=['GET','POST'])
@login_required
def addarticle():
    if request.method == 'POST':
        article = Article(
            nom_art=request.form.get('nom_art'),
            prix_unitaire=request.form.get('prix_unitaire'),
            stock=request.form.get('stock'),
            description=request.form.get('description')
        )
        db.session.add(article)
        db.session.commit()
        return redirect(url_for('routes.article'))

    return render_template("addarticle.html")


@routes.route('/article')
@login_required
def article():
    articles = Article.query.all()

    ventes_par_article = {}
    for a in articles:
        nb_ventes = LigneVente.query.filter_by(id_article=a.id).count()
        ventes_par_article[a.id] = nb_ventes

    return render_template("article.html", articles=articles, ventes_par_article=ventes_par_article)

@routes.route('/modifarticleAffichage')
@login_required
def modifarticleAffiche():
    articles = Article.query.all()
    return render_template("modifarticleAffiche.html", articles=articles)


# ✅ correction route
@routes.route('/modifarticle/<int:id>', methods=['POST'])
@login_required
def modifarticle(id):
    article = Article.query.get(id)

    article.nom_art = request.form.get('nom_art')
    article.prix_unitaire = request.form.get('prix_unitaire')
    article.stock = request.form.get('stock')
    article.description = request.form.get('description')

    db.session.commit()
    return redirect(url_for('routes.modifarticleAffiche'))


# ✅ correction route
@routes.route('/modifarticle/<int:id>', methods=['GET'])
@login_required
def mise_a_jour(id):
    article = Article.query.get(id)
    return render_template('modifarticle.html', article=article)


@routes.route('/supprimarticleAffichage')
@login_required
def supprimarticleAffiche():
    articles = Article.query.all()
    return render_template("supprimarticleAffiche.html", articles=articles)


# ✅ correction route
@routes.route('/supprimarticle/<int:id>')
@login_required
def supprimarticle(id):
    article_delete = Article.query.get_or_404(id)

    deja_vendu = LigneVente.query.filter_by(id_article=id).first() or \
                 Detail_credit.query.filter_by(article=id).first()

    if deja_vendu:
        flash("Impossible de supprimer : cet article a déjà été vendu (historique conservé)", "error")
        return redirect(url_for('routes.article'))

    db.session.delete(article_delete)
    db.session.commit()
    flash("Article supprimé !", "success")
    return redirect(url_for('routes.article'))

# ================= AJOUT VENTE =================

@routes.route('/addvente', methods=['GET','POST'])
@login_required
def addvente():
    if request.method == 'POST':

        id_client = int(request.form.get('client_id'))
        montant_paye = float(request.form.get('montant_paye') or 0)

        articles = request.form.getlist('article_id[]')
        quantites = request.form.getlist('quantite[]')
        prixs = request.form.getlist('prix_unitaire[]')

        # ✅ VERIFICATION DU STOCK AVANT TOUTE CREATION
        lignes_valides = []
        for article_id, quantite, prix in zip(articles, quantites, prixs):
            if not article_id or not quantite or not prix:
                continue

            article_obj = Article.query.get(int(article_id))
            quantite = int(quantite)

            if not article_obj:
                flash(f"Article introuvable", "error")
                return redirect(url_for('routes.addvente'))

            if article_obj.stock < quantite:
                flash(f"Stock insuffisant pour {article_obj.nom_art} (disponible: {article_obj.stock})", "error")
                return redirect(url_for('routes.addvente'))

            lignes_valides.append((article_obj, quantite, float(prix)))

        if not lignes_valides:
            flash("Ajoutez au moins un article", "error")
            return redirect(url_for('routes.addvente'))

        # ✅ CREATION VENTE
        vente = Vente(
            id_client=id_client,
            montant_paye=montant_paye,
            montant_total=0,
            reste=0,
            statut="en cours"
        )

        db.session.add(vente)
        db.session.flush()

        total = 0

        for article_obj, quantite, prix in lignes_valides:
            montant = quantite * prix

            ligne = LigneVente(
                id_vente=vente.id,
                id_article=article_obj.id,
                quantite=quantite,
                prix_unitaire=prix,
                montant=montant
            )

            # ✅ DECREMENT DU STOCK
            article_obj.stock -= quantite

            total += montant
            db.session.add(ligne)

        # ✅ Mise à jour vente
        vente.montant_total = total
        vente.reste = total - vente.montant_paye

        # ✅ Statut automatique
        if vente.montant_paye == 0:
            vente.statut = "credit"
        elif vente.montant_paye < total:
            vente.statut = "precompte"
        else:
            vente.statut = "complet"

        # ================= CREDIT AUTO =================
        if vente.statut in ["credit", "precompte"]:

            credit = Credit(
                montant_total=vente.montant_total,
                statut=vente.statut,
                id_client=vente.id_client
            )

            db.session.add(credit)
            db.session.flush()

            vente.id_credit = credit.id

            for ligne in vente.lignes:
                detail = Detail_credit(
                    quantite=ligne.quantite,
                    prix_unitaire=ligne.prix_unitaire,
                    montant=ligne.montant,
                    montant_payer=vente.montant_paye,
                    rest_a_payer=vente.reste,
                    credit=credit.id,
                    article=ligne.id_article
                )
                db.session.add(detail)

        db.session.commit()

        flash("✅ Vente ajoutée avec succès", "success")
        return redirect(url_for('routes.vente'))

    clients = Client.query.all()
    articles = Article.query.all()
    return render_template("addvente.html", clients=clients, articles=articles)


@routes.route('/vente')
@login_required
def vente():
    ventes = Vente.query.order_by(Vente.id.desc()).all()

    en_retard = {}
    for v in ventes:
        en_retard[v.id] = (
            v.statut in ['credit', 'precompte'] and
            v.date and (datetime.utcnow() - v.date) > timedelta(days=30)
        )

    return render_template("vente.html", ventes=ventes, en_retard=en_retard)


# ================= DETAIL VENTE =================

@routes.route('/vente/<int:id>')
@login_required
def detail_vente(id):
    vente = Vente.query.get_or_404(id)
    return render_template("detail_vente.html", vente=vente)


# ================= SUPPRESSION VENTE =================

@routes.route('/suprimvente/<int:id>')
@login_required
def supprimvente(id):
    vente = Vente.query.get_or_404(id)

    # 🔥 supprimer lignes
    for ligne in vente.lignes:
        db.session.delete(ligne)

    # 🔥 supprimer crédit lié (IMPORTANT)
    if hasattr(vente, 'id_credit') and vente.id_credit:
        credit = Credit.query.get(vente.id_credit)

        if credit:
            for d in credit.details:
                db.session.delete(d)
            db.session.delete(credit)

    db.session.delete(vente)
    db.session.commit()

    flash("Vente supprimée", "success")
    return redirect(url_for('routes.vente'))


# ================= ANNULATION VENTE (soft) =================
@routes.route('/annulervente/<int:id>')
@login_required
def annulervente(id):
    vente = Vente.query.get_or_404(id)

    if vente.statut == "annulee":
        flash("Cette vente est déjà annulée", "error")
        return redirect(url_for('routes.vente'))

    # ✅ REMISE EN STOCK
    for ligne in vente.lignes:
        if ligne.article:
            ligne.article.stock += ligne.quantite

    # ✅ ANNULATION DU CREDIT LIE (soft aussi)
    if vente.id_credit:
        credit = Credit.query.get(vente.id_credit)
        if credit:
            credit.statut = "annulee"

    # ✅ PASSAGE EN STATUT ANNULEE (pas de suppression physique)
    vente.statut = "annulee"

    db.session.commit()

    flash("Vente annulée, stock remis à jour", "success")
    return redirect(url_for('routes.vente'))


# ================= LISTE CREDIT =================


@routes.route('/credit')
@login_required
def credit():
    credits = Credit.query.order_by(Credit.date.desc()).all()

    total_en_cours = 0
    total_solde = 0
    infos_credit = {}

    for c in credits:
        vente_liee = Vente.query.filter_by(id_credit=c.id).first()
        reste = float(vente_liee.reste) if vente_liee else 0

        en_retard = (
            c.statut in ['credit', 'precompte'] and
            (datetime.utcnow() - c.date) > timedelta(days=30)
        )

        infos_credit[c.id] = {'reste': reste, 'en_retard': en_retard}

        if c.statut == 'complet':
            total_solde += float(c.montant_total)
        elif c.statut != 'annulee':
            total_en_cours += reste

    return render_template(
        "credit.html",
        credits=credits,
        infos_credit=infos_credit,
        total_en_cours=total_en_cours,
        total_solde=total_solde
    )


# ================= DETAIL CREDIT =================

@routes.route('/detail_credit/<int:id>')
@login_required
def detail_credit(id):
    credit = Credit.query.get_or_404(id)
    return render_template("detail_credit.html", detail_credits=credit.details)

@routes.route('/listedetailcredit')
@login_required
def liste_detail_credit():
    detail_credits = Detail_credit.query.all()
    return render_template("detail_credit.html", detail_credits=detail_credits)


# ================= UTILISATEUR =================

@routes.route('/addutilisateur', methods=['GET','POST'])
#@login_required
def addutilisateur():
    if request.method == 'POST':
        nom_user = request.form.get('nom_user')
        mot_de_passe = request.form.get('mot_de_passe')
        telephone = request.form.get('telephone')
        role = request.form.get('role')

        if len(nom_user) < 1:
            flash("nom trop court", "error")
        elif len(mot_de_passe) < 1:
            flash("mot de passe trop court", "error")
        elif len(telephone) < 1:
            flash("telephone invalide", "error")
        elif len(role) < 2:
            flash("role invalide", "error")
        else:
            # HASHAGE ICI ✅
            mot_de_passe_hash = generate_password_hash(mot_de_passe)

            new_utilisateur = Utilisateur(
                nom_user=nom_user,
                mot_de_passe=mot_de_passe_hash,
                telephone=telephone,
                role=role
            )

            db.session.add(new_utilisateur)
            db.session.commit()
            flash("utilisateur ajouté !", "success")
            return redirect(url_for('routes.utilisateur'))

    return render_template("addutilisateur.html")


@routes.route('/utilisateur')
@login_required
def utilisateur():
    utilisateurs = Utilisateur.query.all()
    return render_template("utilisateur.html", utilisateurs=utilisateurs)


@routes.route('/modifutilisateurAffichage')
@login_required
def modifutilisateurAffiche():
    utilisateurs = Utilisateur.query.all()
    return render_template("modifutilisateurAffiche.html", utilisateurs=utilisateurs)


# CORRECTION ROUTE ❌ -> <int:id>
@routes.route('/modifutilisateur/<int:id>', methods=['POST'])
@login_required
def modifutilisateur(id):
    utilisateur = Utilisateur.query.get_or_404(id)

    utilisateur.nom_user = request.form.get('nom_user')
    utilisateur.telephone = request.form.get('telephone')
    utilisateur.role = request.form.get('role')

    # HASHAGE SI MODIFIÉ ✅
    if request.form.get('mot_de_passe'):
        utilisateur.mot_de_passe = generate_password_hash(request.form.get('mot_de_passe'))

    db.session.commit()
    flash("utilisateur modifié !", "success")
    return redirect(url_for('routes.modifutilisateurAffiche'))


@routes.route('/modifutilisateur/<int:id>', methods=['GET'])
@login_required
def utilisateur_update(id):
    utilisateur = Utilisateur.query.get_or_404(id)
    return render_template('modifutilisateur.html', utilisateur=utilisateur)


@routes.route('/supprimutilisateurAffichage')
@login_required
def supprimutilisateurAffiche():
    utilisateurs = Utilisateur.query.all()
    return render_template("supprimutilisateurAffiche.html", utilisateurs=utilisateurs)


# CORRECTION ROUTE ❌ -> <int:id>
@routes.route('/supprimutilisateur/<int:id>')
@login_required
def supprimutilisateur(id):
    delete_utilisateur = Utilisateur.query.get_or_404(id)

    db.session.delete(delete_utilisateur)
    db.session.commit()

    flash("utilisateur supprimé !", "success")
    return redirect(url_for('routes.supprimutilisateurAffiche'))




# ================= VERSER UN PAIEMENT =================
@routes.route('/vente/<int:id>/payer', methods=['GET', 'POST'])
@login_required
def payer_vente(id):
    vente = Vente.query.get_or_404(id)

    if vente.statut == "annulee":
        flash("Impossible de payer une vente annulée", "error")
        return redirect(url_for('routes.detail_vente', id=vente.id))

    if vente.statut == "complet":
        flash("Cette vente est déjà entièrement payée", "error")
        return redirect(url_for('routes.detail_vente', id=vente.id))

    if request.method == 'POST':
        montant = float(request.form.get('montant') or 0)

        if montant <= 0:
            flash("Le montant doit être supérieur à 0", "error")
            return redirect(url_for('routes.payer_vente', id=id))

        if montant > float(vente.reste):
            flash(f"Le montant dépasse le reste à payer ({vente.reste} FCFA)", "error")
            return redirect(url_for('routes.payer_vente', id=id))

        # ✅ ENREGISTREMENT DU PAIEMENT
        paiement = Paiement(id_vente=vente.id, montant=montant)
        db.session.add(paiement)

        # ✅ MISE A JOUR DE LA VENTE
        vente.montant_paye = float(vente.montant_paye) + montant
        vente.reste = float(vente.montant_total) - vente.montant_paye

        if vente.reste <= 0:
            vente.statut = "complet"
        else:
            vente.statut = "precompte"

        # ✅ MISE A JOUR DU CREDIT LIE + DE SES DETAILS (❗ CE QUI MANQUAIT)
        if vente.id_credit:
            credit = Credit.query.get(vente.id_credit)
            if credit:
                credit.statut = vente.statut

                for detail in credit.details:
                    detail.montant_payer = vente.montant_paye
                    detail.rest_a_payer = vente.reste

        db.session.commit()

        flash(f"✅ Paiement de {montant} FCFA enregistré", "success")
        return redirect(url_for('routes.detail_vente', id=vente.id))

    return render_template("payer_vente.html", vente=vente)