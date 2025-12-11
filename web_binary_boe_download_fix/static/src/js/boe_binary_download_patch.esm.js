import { BinaryField } from "@web/views/fields/binary/binary_field";
import { downloadFile } from "@web/core/network/download";
import { patch } from "@web/core/utils/patch";

patch(BinaryField.prototype, {
  /**
   * Sobrescribe la descarga de ficheros binarios SOLO para:
   *   modelo: l10n.es.aeat.report.export_to_boe
   *   campo:  data
   *
   * Esto cubre TODOS los wizards de "Exportar a BOE" de l10n_es_aeat
   * (mod130, mod303, mod390, etc.), porque todos usan el mismo modelo
   * transitorio y el mismo campo.
   *
   * Para el resto de casos, se llama al comportamiento estándar.
   */
  async onFileDownload() {
    const payload = this.getDownloadData();

    if (
      payload.model === "l10n.es.aeat.report.export_to_boe" &&
      payload.field === "data"
    ) {
      const model = encodeURIComponent(payload.model);
      const id = payload.id;
      const field = encodeURIComponent(payload.field);
      const filename = payload.filename
        ? encodeURIComponent(payload.filename)
        : "";

      // URL REST estándar de Odoo 18 para binarios:
      // /web/content/<model>/<id>/<field>/<filename>?download=true
      let url = `/web/content/${model}/${id}/${field}`;
      if (filename) {
        url += `/${filename}`;
      }
      url += `?download=true`;

      return downloadFile._download(url);
    }

    // Otros binarios: comportamiento original
    return super.onFileDownload();
  },
});
