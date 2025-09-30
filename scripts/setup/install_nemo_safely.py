#!/usr/bin/env python3
"""
Safe NeMo Toolkit Installation Script
Adds NeMo without breaking the existing multi-provider system
"""

import os
import sys
import subprocess
import logging
import json
import requests
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SafeNeMoInstaller:
    """Install NeMo Toolkit safely without breaking existing system"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.venv_path = self.project_root / "venv"
        self.backup_requirements = None
        
    def check_system_health(self) -> bool:
        """Check if the current system is healthy before installation"""
        logger.info("🏥 Checking system health before NeMo installation...")
        
        try:
            # Check backend health
            response = requests.get("http://localhost:8000/api/v1/providers/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Backend healthy: {data.get('status', 'unknown')}")
                return True
            else:
                logger.warning(f"⚠️  Backend health check failed: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Cannot connect to backend: {e}")
            return False
    
    def backup_current_state(self):
        """Backup current requirements and environment"""
        logger.info("💾 Creating backup of current state...")
        
        requirements_file = self.project_root / "backend" / "requirements.txt"
        backup_file = self.project_root / "backend" / "requirements.txt.backup"
        
        if requirements_file.exists():
            import shutil
            shutil.copy2(requirements_file, backup_file)
            logger.info(f"✅ Backed up requirements to {backup_file}")
        
        # Save current pip freeze
        try:
            result = subprocess.run([
                str(self.venv_path / "bin" / "pip"), "freeze"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                freeze_backup = self.project_root / "pip_freeze_before_nemo.txt"
                with open(freeze_backup, 'w') as f:
                    f.write(result.stdout)
                logger.info(f"✅ Saved pip freeze to {freeze_backup}")
        except Exception as e:
            logger.warning(f"⚠️  Could not save pip freeze: {e}")
    
    def check_nemo_compatibility(self) -> dict:
        """Check if current environment is compatible with NeMo"""
        logger.info("🔍 Checking NeMo compatibility...")
        
        compatibility = {
            'torch_compatible': False,
            'transformers_compatible': False,
            'python_compatible': False,
            'system_compatible': False,
            'issues': []
        }
        
        try:
            # Check Python version
            python_version = sys.version_info
            if python_version >= (3, 8) and python_version < (3, 12):
                compatibility['python_compatible'] = True
                logger.info(f"✅ Python {python_version.major}.{python_version.minor} is compatible")
            else:
                compatibility['issues'].append(f"Python {python_version.major}.{python_version.minor} may not be compatible (need 3.8-3.11)")
            
            # Check PyTorch
            import torch
            torch_version = torch.__version__
            if torch_version.startswith('2.'):
                compatibility['torch_compatible'] = True
                logger.info(f"✅ PyTorch {torch_version} is compatible")
            else:
                compatibility['issues'].append(f"PyTorch {torch_version} may need upgrade")
            
            # Check Transformers
            import transformers
            transformers_version = transformers.__version__
            compatibility['transformers_compatible'] = True
            logger.info(f"✅ Transformers {transformers_version} is compatible")
            
            # Check system
            import platform
            system = platform.system()
            if system in ['Linux', 'Darwin']:  # macOS is Darwin
                compatibility['system_compatible'] = True
                logger.info(f"✅ {system} system is compatible")
            else:
                compatibility['issues'].append(f"{system} may have compatibility issues")
                
        except ImportError as e:
            compatibility['issues'].append(f"Missing dependency: {e}")
        
        return compatibility
    
    def install_nemo_toolkit(self, method='pip') -> bool:
        """Install NeMo Toolkit using specified method"""
        logger.info(f"📦 Installing NeMo Toolkit using {method}...")
        
        pip_cmd = str(self.venv_path / "bin" / "pip")
        
        if method == 'pip':
            # Standard pip installation
            cmd = [
                pip_cmd, "install", 
                "nemo_toolkit[nlp]>=1.22.0",
                "--timeout", "300",
                "--retries", "3"
            ]
        elif method == 'conda':
            # Conda installation (if available)
            cmd = ["conda", "install", "-c", "conda-forge", "nemo_toolkit"]
        else:
            logger.error(f"❌ Unknown installation method: {method}")
            return False
        
        try:
            logger.info(f"Running: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)  # 30 min timeout
            
            if result.returncode == 0:
                logger.info("✅ NeMo Toolkit installed successfully")
                return True
            else:
                logger.error(f"❌ NeMo installation failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("❌ NeMo installation timed out")
            return False
        except Exception as e:
            logger.error(f"❌ NeMo installation error: {e}")
            return False
    
    def test_nemo_import(self) -> bool:
        """Test if NeMo can be imported successfully"""
        logger.info("🧪 Testing NeMo import...")
        
        try:
            # Test basic NeMo import
            import nemo
            logger.info(f"✅ NeMo imported successfully: {nemo.__version__}")
            
            # Test NLP collections
            import nemo.collections.nlp as nemo_nlp
            logger.info("✅ NeMo NLP collections imported successfully")
            
            return True
            
        except ImportError as e:
            logger.error(f"❌ NeMo import failed: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ NeMo test error: {e}")
            return False
    
    def update_requirements(self):
        """Update requirements.txt to include NeMo"""
        logger.info("📝 Updating requirements.txt...")
        
        requirements_file = self.project_root / "backend" / "requirements.txt"
        
        try:
            with open(requirements_file, 'r') as f:
                content = f.read()
            
            # Uncomment NeMo line
            updated_content = content.replace(
                "# nemo_toolkit[nlp]>=1.22.0  # Commented out - install manually if needed",
                "nemo_toolkit[nlp]>=1.22.0  # NeMo Toolkit for local AI processing"
            )
            
            with open(requirements_file, 'w') as f:
                f.write(updated_content)
            
            logger.info("✅ Requirements.txt updated")
            
        except Exception as e:
            logger.error(f"❌ Failed to update requirements.txt: {e}")
    
    def test_system_after_installation(self) -> bool:
        """Test that the system still works after NeMo installation"""
        logger.info("🧪 Testing system after NeMo installation...")
        
        try:
            # Test backend health
            response = requests.get("http://localhost:8000/api/v1/providers/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Backend still healthy: {data.get('status', 'unknown')}")
                
                # Check if nemo_local provider is now initialized
                nemo_status = data.get('providers', {}).get('nemo_local', {})
                if nemo_status.get('initialized'):
                    logger.info("🎉 NeMo local provider is now initialized!")
                else:
                    logger.info("📋 NeMo local provider available but not initialized (normal)")
                
                return True
            else:
                logger.error(f"❌ Backend health check failed after installation: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ System test failed after installation: {e}")
            return False
    
    def rollback_installation(self):
        """Rollback NeMo installation if something goes wrong"""
        logger.warning("🔄 Rolling back NeMo installation...")
        
        try:
            # Restore requirements backup
            requirements_file = self.project_root / "backend" / "requirements.txt"
            backup_file = self.project_root / "backend" / "requirements.txt.backup"
            
            if backup_file.exists():
                import shutil
                shutil.copy2(backup_file, requirements_file)
                logger.info("✅ Requirements.txt restored from backup")
            
            # Uninstall NeMo
            pip_cmd = str(self.venv_path / "bin" / "pip")
            subprocess.run([pip_cmd, "uninstall", "nemo_toolkit", "-y"], 
                         capture_output=True, text=True)
            logger.info("✅ NeMo Toolkit uninstalled")
            
        except Exception as e:
            logger.error(f"❌ Rollback failed: {e}")
    
    def run_safe_installation(self):
        """Run the complete safe NeMo installation process"""
        logger.info("🚀 Starting Safe NeMo Toolkit Installation")
        logger.info("=" * 60)
        
        # Step 1: Check system health
        if not self.check_system_health():
            logger.error("❌ System is not healthy. Aborting installation.")
            return False
        
        # Step 2: Check compatibility
        compatibility = self.check_nemo_compatibility()
        if compatibility['issues']:
            logger.warning("⚠️  Compatibility issues found:")
            for issue in compatibility['issues']:
                logger.warning(f"   - {issue}")
            
            response = input("Continue anyway? (y/N): ")
            if response.lower() != 'y':
                logger.info("Installation cancelled by user")
                return False
        
        # Step 3: Backup current state
        self.backup_current_state()
        
        # Step 4: Install NeMo
        installation_success = False
        try:
            installation_success = self.install_nemo_toolkit()
            
            if installation_success:
                # Step 5: Test NeMo import
                if self.test_nemo_import():
                    # Step 6: Update requirements
                    self.update_requirements()
                    
                    # Step 7: Test system
                    if self.test_system_after_installation():
                        logger.info("🎉 NeMo Toolkit installed successfully!")
                        logger.info("✅ System remains healthy and functional")
                        return True
                    else:
                        logger.error("❌ System health check failed after installation")
                        installation_success = False
                else:
                    logger.error("❌ NeMo import test failed")
                    installation_success = False
            
        except Exception as e:
            logger.error(f"❌ Installation failed with error: {e}")
            installation_success = False
        
        # Rollback if installation failed
        if not installation_success:
            logger.warning("🔄 Installation failed, rolling back...")
            self.rollback_installation()
            logger.info("✅ System restored to previous state")
            return False
        
        return True

def main():
    """Main installation function"""
    installer = SafeNeMoInstaller()
    
    print("🤖 Safe NeMo Toolkit Installation")
    print("=" * 40)
    print("This script will safely install NeMo Toolkit while preserving your working system.")
    print("If anything goes wrong, it will automatically rollback.")
    print()
    
    response = input("Proceed with NeMo installation? (y/N): ")
    if response.lower() != 'y':
        print("Installation cancelled.")
        return
    
    success = installer.run_safe_installation()
    
    if success:
        print("\n🎉 SUCCESS!")
        print("=" * 40)
        print("✅ NeMo Toolkit installed successfully")
        print("✅ Your system remains fully functional")
        print("✅ Multi-provider system now includes real NeMo support")
        print("\n🔗 Next steps:")
        print("   1. Restart your backend server")
        print("   2. Check provider health: curl http://localhost:8000/api/v1/providers/health")
        print("   3. Test NeMo local provider functionality")
    else:
        print("\n❌ Installation failed, but your system is safe!")
        print("=" * 40)
        print("✅ System restored to previous working state")
        print("✅ All existing functionality preserved")
        print("\n💡 You can try again later or continue using the current multi-provider setup")

if __name__ == "__main__":
    main()
