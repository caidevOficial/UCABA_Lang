fn main() {
    #[cfg(windows)]
    {
        let mut res = winres::WindowsResource::new();
        res.set_icon("../../ucaba_icon.ico");
        res.set("ProductName", "Instalador UCABA");
        res.set("FileDescription", "Instalador Gráfico Todo-en-Uno del Lenguaje UCABA");
        res.set("LegalCopyright", "Copyright (c) 2026 Facu Falcone");
        res.set("FileVersion", "2.0.0.0");
        res.set("ProductVersion", "2.0.0.0");
        if let Err(e) = res.compile() {
            eprintln!("Warning: could not compile Windows resource: {}", e);
        }
    }
}
