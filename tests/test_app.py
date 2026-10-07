from models import Equipamento, Usuario


def test_rota_protegida_redireciona_para_login(client):
    resp = client.get("/")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_login_com_credenciais_invalidas(client, login):
    resp = login(senha="errada")
    assert resp.status_code == 200
    assert "Credenciais inválidas" in resp.get_data(as_text=True)


def test_login_valido_e_logout(client, login):
    resp = login()
    assert resp.status_code == 302
    assert client.get("/").status_code == 200
    assert client.get("/logout").status_code == 302
    assert client.get("/").status_code == 302


def test_cadastro_e_consulta_de_equipamento(client, login):
    login()
    dados = {
        "tipo": "Notebook", "marca": "Dell", "modelo": "Inspiron", "num_serie": "ABC123",
        "localizacao": "Sede", "status": "Em uso", "valor": "3000",
    }
    resp = client.post("/cadastrar", data=dados)
    assert resp.status_code == 302

    equipamento = Equipamento.query.filter_by(num_serie="ABC123").one()
    assert equipamento.id_publico == "PAT-001"

    resp = client.post("/consulta", data={"busca": "ABC123"})
    assert resp.status_code == 200


def test_termo_de_cautela_gera_pdf(client, login):
    login()
    client.post("/cadastrar", data={
        "tipo": "Notebook", "marca": "Dell", "modelo": "X", "num_serie": "S1",
        "localizacao": "Sede", "status": "Em uso", "responsavel": "Fulano",
    })
    resp = client.get("/gerar_termo_cautela/PAT-001")
    assert resp.status_code == 200
    assert resp.data.startswith(b"%PDF")


def test_usuario_comum_nao_acessa_admin(client, login):
    login("leitor")
    resp = client.get("/admin/usuarios")
    assert resp.status_code == 302


def test_upload_termo_rejeita_arquivo_que_nao_e_pdf(client, login):
    from io import BytesIO
    login()
    client.post("/cadastrar", data={
        "tipo": "Notebook", "marca": "Dell", "modelo": "X", "num_serie": "S2",
        "localizacao": "Sede", "status": "Em uso",
    })
    resp = client.post(
        "/upload_termo/PAT-001",
        data={"termo": (BytesIO(b"nao e pdf"), "falso.pdf")},
        content_type="multipart/form-data",
    )
    assert resp.status_code == 200
    assert "PDF válido" in resp.get_data(as_text=True)
    assert Equipamento.query.filter_by(id_publico="PAT-001").one().termo_pdf_path is None


def test_pagina_404_customizada(client, login):
    login()
    assert client.get("/nao-existe").status_code == 404


def test_cli_create_admin_exige_senha_forte(app):
    runner = app.test_cli_runner()
    resp = runner.invoke(args=["create-admin", "--username", "novo", "--password", "fraca"])
    assert resp.exit_code != 0

    resp = runner.invoke(args=["create-admin", "--username", "novo", "--password", "Forte1234"])
    assert resp.exit_code == 0
    assert Usuario.query.filter_by(username="novo", nivel_acesso=3).one()
