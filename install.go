package main

import (
	"archive/zip"
	"fmt"
	"io"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
)

func main() {
	// Vérifie si le module chess est installé
	cmd := exec.Command("pip", "show", "chess")
	if err := cmd.Run(); err != nil {
		fmt.Println("Le module 'chess' n'est pas installé. Installation...")
		install := exec.Command("pip", "install", "--user", "chess")
		install.Stdout = os.Stdout
		install.Stderr = os.Stderr
		_ = install.Run()
	} else {
		fmt.Println("Le module 'chess' est déjà installé.")
	}

	// Chemin vers PyChess.py
	scriptPath, err := filepath.Abs("PyChess.py")
	if err != nil {
		fmt.Println("Erreur pour récupérer le chemin absolu :", err)
		return
	}

	// Vérifier si pythonw existe
	pythonExe := "python"
	if _, err := exec.LookPath("pythonw"); err == nil {
		pythonExe = "pythonw"
	}

	ensureStockfishInstalled()

	// Créer le raccourci sur le Bureau
	desktop := filepath.Join(os.Getenv("USERPROFILE"), "Desktop")
	lnkPath := filepath.Join(desktop, "PyChess.lnk")

	err = createShortcut(pythonExe, scriptPath, lnkPath)
	if err != nil {
		fmt.Println("Erreur lors de la création du raccourci :", err)
	} else {
		fmt.Println("Raccourci créé :", lnkPath)
	}

	// Lancer PyChess
	exec.Command(pythonExe, scriptPath).Start()
}

func createShortcut(pythonExe, target, lnkPath string) error {
	// Chemin de l'icône (ex: fichier .ico à côté du script)
	iconPath := filepath.Join(filepath.Dir(target), "chessIcon.ico")

	vbs := fmt.Sprintf(`Set oWS = WScript.CreateObject("WScript.Shell")
sLinkFile = "%s"
Set oLink = oWS.CreateShortcut(sLinkFile)
oLink.TargetPath = "%s"
oLink.Arguments = "%s"
oLink.WorkingDirectory = "%s"
oLink.IconLocation = "%s"
oLink.Save
`, lnkPath, pythonExe, target, filepath.Dir(target), iconPath)

	tmpVbs := filepath.Join(os.TempDir(), "create_link.vbs")
	err := os.WriteFile(tmpVbs, []byte(vbs), 0644)
	if err != nil {
		return err
	}
	defer os.Remove(tmpVbs)

	return exec.Command("wscript", tmpVbs).Run()
}

// Appelé depuis main()
func ensureStockfishInstalled() error {
	stockfishPath := filepath.Join("stockfish-windows-x86-64-avx2", "stockfish", "stockfish-windows-x86-64-avx2.exe")

	if _, err := os.Stat(stockfishPath); err == nil {
		fmt.Println("Stockfish est déjà présent.")
		return nil
	}

	fmt.Println("Stockfish manquant. Téléchargement...")

	url := "https://example.com/stockfish.zip" // ⚠️ Remplace par une vraie URL directe vers ton ZIP contenant le binaire
	zipPath := filepath.Join(os.TempDir(), "stockfish.zip")

	// Télécharger le fichier ZIP
	out, err := os.Create(zipPath)
	if err != nil {
		return err
	}
	defer out.Close()

	resp, err := http.Get(url)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	_, err = io.Copy(out, resp.Body)
	if err != nil {
		return err
	}

	// Extraire le fichier ZIP
	return unzip(zipPath, filepath.Join("stockfish-windows-x86-64-avx2", "stockfish"))
}

// Fonction d'extraction ZIP
func unzip(src, dest string) error {
	r, err := zip.OpenReader(src)
	if err != nil {
		return err
	}
	defer r.Close()

	os.MkdirAll(dest, 0755)

	for _, f := range r.File {
		fpath := filepath.Join(dest, f.Name)

		if f.FileInfo().IsDir() {
			os.MkdirAll(fpath, f.Mode())
			continue
		}

		if err := os.MkdirAll(filepath.Dir(fpath), 0755); err != nil {
			return err
		}

		outFile, err := os.OpenFile(fpath, os.O_WRONLY|os.O_CREATE|os.O_TRUNC, f.Mode())
		if err != nil {
			return err
		}

		rc, err := f.Open()
		if err != nil {
			return err
		}

		_, err = io.Copy(outFile, rc)

		outFile.Close()
		rc.Close()

		if err != nil {
			return err
		}
	}

	return nil
}
