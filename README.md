# 📦 Sistema de Controle de Estoque para Campanha

Sistema web leve e intuitivo desenvolvido em **Python (Flask)** e **SQLite** para gerenciar entradas, saídas, devoluções, montagem de kits e o estoque atual de materiais de forma centralizada. Desenvolvido com foco em agilidade, segurança e responsividade para uso em campo ou escritório.

---

## 🚀 Tecnologias Utilizadas
* **Backend:** Python, Flask
* **Banco de Dados:** SQLite
* **Frontend:** Bootstrap 5, FontAwesome
* **Controle de Acesso:** Sistema de login com sessões protegidas

---

## ✨ Principais Funcionalidades
* **Painel Administrativo (Dashboard):** Visão geral de todas as movimentações com ferramentas de busca, filtros por tipo e paginação.
* **Controle de Estoque Consolidado:** Cálculo automático de saldo atual com indicadores visuais (cards) de entradas, saídas e itens esgotados.
* **Montagem de Kits:** Sistema inteligente que dá baixa em múltiplos materiais de uma só vez, com **validação prévia para impedir estoque negativo**.
* **Geração de Recibos e Relatórios:** Termos de recebimento de kits e opções de impressão/PDF estruturadas.
* **Gestão e Segurança:** Cadastro de operadores/administradores, gerenciamento de materiais e ferramentas de exportação/importação de backup do banco de dados.

---

## ⚙️ Como Executar o Projeto Localmente

Siga os passos abaixo para rodar o sistema na sua máquina:

1. **Clone o repositório:**
   ```bash
   git clone [https://github.com/ronaldbass27/controle-campana.git](https://github.com/ronaldbass27/controle-campana.git)
   cd controle-campana
