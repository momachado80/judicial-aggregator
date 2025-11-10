# Verificar o endpoint atual
with open('src/main.py', 'r') as f:
    content = f.read()
    if 'relevancia' in content:
        print("✅ Parâmetro 'relevancia' já existe na API")
    else:
        print("❌ Precisa adicionar parâmetro 'relevancia'")
