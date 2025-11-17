from dje_downloader import baixar_dje_tjsp
from dje_parser import extrair_processos_dje
from datetime import datetime, timedelta
import json

def processar_periodo(dias_atras: int = 30, caderno: str = "11"):
    """
    Baixa e processa DJE de múltiplos dias
    
    Args:
        dias_atras: Quantos dias para trás buscar
        caderno: Caderno (11 = Judicial 1ª Instância Interior)
    """
    print(f"🔍 Processando últimos {dias_atras} dias...")
    
    hoje = datetime.now()
    todos_processos = []
    
    for i in range(dias_atras):
        data = hoje - timedelta(days=i)
        data_str = data.strftime("%d/%m/%Y")
        
        print(f"\n{'='*80}")
        print(f"📅 DIA {i+1}/{dias_atras}: {data_str}")
        print('='*80)
        
        # Pular finais de semana (sábado=5, domingo=6)
        if data.weekday() >= 5:
            print("⏭️  Pulando (final de semana)")
            continue
        
        # Baixar PDF
        pdf_path = baixar_dje_tjsp(data_str, caderno)
        
        if not pdf_path:
            print("❌ Falha no download")
            continue
        
        # Parsear
        processos = extrair_processos_dje(pdf_path)
        
        # Adicionar data
        for p in processos:
            p['data_dje'] = data_str
        
        todos_processos.extend(processos)
        
        print(f"✅ {len(processos)} processos neste dia")
        print(f"📊 Total acumulado: {len(todos_processos)}")
    
    # Salvar resultado
    output_file = "data/processos_30dias.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(todos_processos, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'='*80}")
    print(f"🎉 PROCESSAMENTO COMPLETO!")
    print(f"{'='*80}")
    print(f"Total de processos: {len(todos_processos)}")
    print(f"Salvo em: {output_file}")
    
    # Estatísticas
    from collections import Counter
    
    print(f"\n📊 POR TIPO:")
    tipos = Counter(p['tipo'] for p in todos_processos)
    for tipo, count in tipos.items():
        print(f"   {tipo}: {count}")
    
    print(f"\n📍 POR COMARCA (top 10):")
    comarcas = Counter(p['comarca'] for p in todos_processos)
    for comarca, count in comarcas.most_common(10):
        print(f"   {comarca}: {count}")
    
    return todos_processos

if __name__ == "__main__":
    # Processar últimos 30 dias
    processos = processar_periodo(dias_atras=30, caderno="11")
