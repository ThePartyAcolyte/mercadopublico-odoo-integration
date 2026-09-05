def migrate(cr, version):
    if not version:
        return

    model_mapping = {
        'mercadopublico.etapa': 'mercadopublico.stage',
        'mercadopublico.filtro': 'mercadopublico.keyword',
        'mercadopublico.organismo': 'mercadopublico.buyer',
        'mercadopublico.categoria': 'mercadopublico.category',
        'mercadopublico.licitacion': 'mercadopublico.tender',
        'mercadopublico.licitacion.item': 'mercadopublico.tender.item',
        'mercadopublico.ubicacion': 'mercadopublico.location',
    }

    for old_model, new_model in model_mapping.items():
        # Update ir_model_data (External IDs)
        cr.execute("""
            UPDATE ir_model_data
            SET model = %s
            WHERE model = %s
        """, (new_model, old_model))

        # Rename tables in database
        old_table = old_model.replace('.', '_')
        new_table = new_model.replace('.', '_')
        
        cr.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = %s)", (old_table,))
        if cr.fetchone()[0]:
            cr.execute(f"ALTER TABLE {old_table} RENAME TO {new_table}")
            
        cr.execute("UPDATE ir_act_window SET res_model = %s WHERE res_model = %s", (new_model, old_model))
