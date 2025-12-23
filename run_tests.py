#!/usr/bin/env python
"""
Script para ejecutar todos los tests del sistema
"""
import os
import sys
import subprocess
import time
from pathlib import Path

def check_docker_services():
    """Verificar que los servicios de Docker estén ejecutándose"""
    print("🔍 Verificando servicios de Docker...")
    
    try:
        result = subprocess.run(['docker-compose', 'ps'], 
                              capture_output=True, text=True, check=True)
        
        if 'Up' in result.stdout:
            print("✅ Servicios de Docker están ejecutándose")
            return True
        else:
            print("❌ Los servicios de Docker no están ejecutándose")
            return False
    except subprocess.CalledProcessError:
        print("❌ Error al verificar servicios de Docker")
        return False

def wait_for_services():
    """Esperar a que los servicios estén listos"""
    print("⏳ Esperando a que los servicios estén listos...")
    
    max_attempts = 30
    for attempt in range(max_attempts):
        try:
            # Verificar que PostgreSQL esté listo
            result = subprocess.run([
                'docker-compose', 'exec', '-T', 'db', 
                'pg_isready', '-U', 'postgres'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ PostgreSQL está listo")
                break
        except subprocess.CalledProcessError:
            pass
        
        if attempt < max_attempts - 1:
            print(f"⏳ Intento {attempt + 1}/{max_attempts}, esperando...")
            time.sleep(2)
    else:
        print("❌ Timeout esperando a que PostgreSQL esté listo")
        return False
    
    # Esperar un poco más para Redis y otros servicios
    time.sleep(5)
    return True

def run_migrations():
    """Ejecutar migraciones de Django"""
    print("🔄 Ejecutando migraciones...")
    
    try:
        subprocess.run([
            'docker-compose', 'exec', '-T', 'web',
            'python', 'manage.py', 'migrate'
        ], check=True)
        print("✅ Migraciones ejecutadas exitosamente")
        return True
    except subprocess.CalledProcessError:
        print("❌ Error ejecutando migraciones")
        return False

def load_test_data():
    """Cargar datos de prueba"""
    print("📊 Cargando datos de prueba...")
    
    try:
        # Cargar fixtures de prueba
        subprocess.run([
            'docker-compose', 'exec', '-T', 'web',
            'python', 'manage.py', 'loaddata', 'fixtures/test_data.json'
        ], check=True)
        print("✅ Datos de prueba cargados exitosamente")
        return True
    except subprocess.CalledProcessError:
        print("⚠️  Advertencia: No se pudieron cargar algunos datos de prueba (puede ser normal)")
        return True  # No es crítico

def run_unit_tests():
    """Ejecutar tests unitarios"""
    print("🧪 Ejecutando tests unitarios...")
    
    try:
        result = subprocess.run([
            'docker-compose', 'exec', '-T', 'web',
            'python', '-m', 'pytest', 
            '-v',
            '--tb=short',
            '-m', 'unit',
            '--disable-warnings'
        ], check=True, capture_output=True, text=True)
        
        print("✅ Tests unitarios pasaron exitosamente")
        print(f"📊 Resultado:\n{result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        print("❌ Algunos tests unitarios fallaron")
        print(f"📊 Resultado:\n{e.stdout}")
        print(f"❌ Errores:\n{e.stderr}")
        return False

def run_integration_tests():
    """Ejecutar tests de integración"""
    print("🔗 Ejecutando tests de integración...")
    
    try:
        result = subprocess.run([
            'docker-compose', 'exec', '-T', 'web',
            'python', '-m', 'pytest',
            '-v',
            '--tb=short', 
            '-m', 'integration',
            '--disable-warnings'
        ], check=True, capture_output=True, text=True)
        
        print("✅ Tests de integración pasaron exitosamente")
        print(f"📊 Resultado:\n{result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        print("❌ Algunos tests de integración fallaron")
        print(f"📊 Resultado:\n{e.stdout}")
        print(f"❌ Errores:\n{e.stderr}")
        return False

def run_api_tests():
    """Ejecutar tests de API"""
    print("🌐 Ejecutando tests de API...")
    
    try:
        result = subprocess.run([
            'docker-compose', 'exec', '-T', 'web',
            'python', '-m', 'pytest',
            '-v',
            '--tb=short',
            '-m', 'api',
            '--disable-warnings'
        ], check=True, capture_output=True, text=True)
        
        print("✅ Tests de API pasaron exitosamente")
        print(f"📊 Resultado:\n{result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        print("❌ Algunos tests de API fallaron")
        print(f"📊 Resultado:\n{e.stdout}")
        print(f"❌ Errores:\n{e.stderr}")
        return False

def run_all_tests():
    """Ejecutar todos los tests"""
    print("🧪 Ejecutando TODOS los tests...")
    
    try:
        result = subprocess.run([
            'docker-compose', 'exec', '-T', 'web',
            'python', '-m', 'pytest',
            '-v',
            '--tb=short',
            '--disable-warnings',
            '--maxfail=10'  # Parar después de 10 fallos
        ], check=True, capture_output=True, text=True)
        
        print("✅ TODOS los tests pasaron exitosamente")
        print(f"📊 Resultado:\n{result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        print("❌ Algunos tests fallaron")
        print(f"📊 Resultado:\n{e.stdout}")
        print(f"❌ Errores:\n{e.stderr}")
        return False

def test_api_endpoints():
    """Probar algunos endpoints de la API"""
    print("🌐 Probando endpoints de la API...")
    
    endpoints_to_test = [
        '/api/v1/auth/health/',
        '/api/docs/',
        '/api/schema/',
    ]
    
    for endpoint in endpoints_to_test:
        try:
            result = subprocess.run([
                'curl', '-f', '-s', f'http://localhost:8000{endpoint}'
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                print(f"✅ {endpoint} - OK")
            else:
                print(f"❌ {endpoint} - Error")
        except subprocess.TimeoutExpired:
            print(f"⏰ {endpoint} - Timeout")
        except Exception as e:
            print(f"❌ {endpoint} - Error: {e}")

def generate_test_report():
    """Generar reporte de tests"""
    print("📋 Generando reporte de tests...")
    
    try:
        result = subprocess.run([
            'docker-compose', 'exec', '-T', 'web',
            'python', '-m', 'pytest',
            '--tb=short',
            '--disable-warnings',
            '--quiet',
            '--tb=no'
        ], capture_output=True, text=True)
        
        # Crear reporte
        report_content = f"""
# Reporte de Tests - Plataforma de Gestión de Inventario

## Fecha: {time.strftime('%Y-%m-%d %H:%M:%S')}

## Resumen de Ejecución:
{result.stdout}

## Estadísticas:
- Tests ejecutados: {result.stdout.count('PASSED') + result.stdout.count('FAILED')}
- Tests exitosos: {result.stdout.count('PASSED')}
- Tests fallidos: {result.stdout.count('FAILED')}

## Estado General: {'✅ EXITOSO' if result.returncode == 0 else '❌ CON ERRORES'}
"""
        
        with open('test_report.md', 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print("✅ Reporte generado: test_report.md")
        return True
    except Exception as e:
        print(f"❌ Error generando reporte: {e}")
        return False

def main():
    """Función principal"""
    print("🚀 Iniciando suite de tests para Plataforma de Gestión de Inventario")
    print("=" * 70)
    
    # Verificar que estamos en el directorio correcto
    if not Path('manage.py').exists():
        print("❌ Error: No se encontró manage.py. Ejecute desde el directorio raíz del proyecto.")
        sys.exit(1)
    
    # Verificar servicios de Docker
    if not check_docker_services():
        print("❌ Los servicios de Docker no están disponibles. Ejecute 'docker-compose up -d' primero.")
        sys.exit(1)
    
    # Esperar a que los servicios estén listos
    if not wait_for_services():
        print("❌ Los servicios no están listos. Verifique la configuración de Docker.")
        sys.exit(1)
    
    # Ejecutar migraciones
    if not run_migrations():
        print("❌ Error en migraciones. Verifique la configuración de la base de datos.")
        sys.exit(1)
    
    # Cargar datos de prueba
    load_test_data()
    
    # Ejecutar tests según argumentos
    success = True
    
    if len(sys.argv) > 1:
        test_type = sys.argv[1].lower()
        
        if test_type == 'unit':
            success = run_unit_tests()
        elif test_type == 'integration':
            success = run_integration_tests()
        elif test_type == 'api':
            success = run_api_tests()
        elif test_type == 'endpoints':
            test_api_endpoints()
        elif test_type == 'all':
            success = run_all_tests()
        else:
            print(f"❌ Tipo de test desconocido: {test_type}")
            print("Tipos disponibles: unit, integration, api, endpoints, all")
            sys.exit(1)
    else:
        # Ejecutar todos los tests por defecto
        print("🧪 Ejecutando suite completa de tests...")
        success = (
            run_unit_tests() and
            run_integration_tests() and
            run_api_tests()
        )
        
        # Probar endpoints
        test_api_endpoints()
    
    # Generar reporte
    generate_test_report()
    
    # Resultado final
    print("=" * 70)
    if success:
        print("🎉 ¡TODOS LOS TESTS PASARON EXITOSAMENTE!")
        print("✅ El sistema está funcionando correctamente")
        print("📋 Revise test_report.md para detalles completos")
    else:
        print("❌ ALGUNOS TESTS FALLARON")
        print("🔍 Revise los errores arriba y test_report.md para más detalles")
        sys.exit(1)

if __name__ == '__main__':
    main()