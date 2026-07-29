/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, useState, onWillStart, useRef, useEffect } from "@odoo/owl";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { useService } from "@web/core/utils/hooks";
import { CategoryCheckbox } from "./categoria_tree_widget"; // Reusamos el checkbox genérico

export class UbicacionTreeWidget extends Component {
    static template = "MercadoPublico.UbicacionTreeWidget";
    static components = { CategoryCheckbox };
    static props = {
        ...standardFieldProps,
    };

    setup() {
        this.orm = useService("orm");
        this.state = useState({
            categories: [], 
            tree: [], 
            searchQuery: "",
            expandedNodes: {}, // Use object for reactivity
        });

        onWillStart(async () => {
            await this.loadCategories();
        });
    }

    get selectedIds() {
        const relationList = this.props.record.data[this.props.name];
        if (!relationList || !relationList.records) return [];
        return relationList.records.map(r => r.resId || r.data.id);
    }

    getCheckboxState(node) {
        const selected = new Set(this.selectedIds);
        if (selected.has(node.id)) {
            return { checked: true, indeterminate: false };
        }
        
        const hasSelectedDescendant = (n) => {
            if (selected.has(n.id)) return true;
            return n.children.some(child => hasSelectedDescendant(child));
        };
        
        if (node.children.some(child => hasSelectedDescendant(child))) {
            return { checked: false, indeterminate: true };
        }
        
        return { checked: false, indeterminate: false };
    }

    async loadCategories() {
        const categories = await this.orm.searchRead(
            "mercadopublico.location",
            [],
            ["id", "name", "tipo", "parent_id"],
            { order: "name ASC" }
        );
        
        const map = new Map();
        const tree = [];
        
        categories.forEach(cat => {
            map.set(cat.id, { 
                id: cat.id,
                name: cat.name,
                tipo: cat.tipo,
                parent_id: cat.parent_id ? cat.parent_id[0] : null,
                children: [],
                expanded: false,
                visible: true
            });
        });

        categories.forEach(cat => {
            const node = map.get(cat.id);
            if (node.parent_id) {
                const parent = map.get(node.parent_id);
                if (parent) {
                    parent.children.push(node);
                } else {
                    tree.push(node);
                }
            } else {
                tree.push(node);
            }
        });

        this.categoryMap = map;
        this.state.categories = Array.from(map.values());
        this.state.tree = tree;
    }

    toggleExpand(nodeId) {
        this.state.expandedNodes[nodeId] = !this.state.expandedNodes[nodeId];
    }

    async toggleSelection(node, ev) {
        const checked = ev.target.checked;
        const currentSelectedIds = new Set(this.selectedIds);

        // Recursive function to toggle children
        const toggleChildren = (n, isChecked) => {
            if (isChecked) {
                currentSelectedIds.add(n.id);
            } else {
                currentSelectedIds.delete(n.id);
            }
            n.children.forEach(child => toggleChildren(child, isChecked));
        };

        toggleChildren(node, checked);

        await this.props.record.update({
            [this.props.name]: [
                [6, 0, Array.from(currentSelectedIds)]
            ]
        });
    }

    onSearchInput(ev) {
        const query = ev.target.value.toLowerCase();
        if (this.searchTimeout) {
            clearTimeout(this.searchTimeout);
        }
        this.searchTimeout = setTimeout(() => {
            this.executeSearch(query);
        }, 300);
    }

    executeSearch(query) {
        this.state.searchQuery = query;
        if (!query) {
            this.state.categories.forEach(node => {
                node.visible = true;
            });
            return;
        }

        // Reset visibility
        this.state.categories.forEach(node => {
            node.visible = false;
            node.isMatch = false;
        });

        // 1. Mark direct matches
        this.state.categories.forEach(node => {
            const match = node.name.toLowerCase().includes(query);
            if (match) {
                node.isMatch = true;
            }
        });

        // 2. Propagate visibility to parents and children
        this.state.categories.forEach(node => {
            if (node.isMatch) {
                node.visible = true;
                
                // Parents visible and expanded
                let currentParentId = node.parent_id;
                while (currentParentId) {
                    const parentNode = this.categoryMap.get(currentParentId);
                    if (parentNode) {
                        parentNode.visible = true;
                        this.state.expandedNodes[currentParentId] = true;
                        currentParentId = parentNode.parent_id;
                    } else {
                        break;
                    }
                }
                
                // Children visible
                const makeChildrenVisible = (n) => {
                    n.children.forEach(child => {
                        child.visible = true;
                        makeChildrenVisible(child);
                    });
                };
                makeChildrenVisible(node);
            }
        });
    }

    isNodeVisible(node) {
        return node.visible;
    }
}

export const ubicacionTreeWidget = {
    component: UbicacionTreeWidget,
    supportedTypes: ["many2many"],
};

registry.category("fields").add("ubicacion_tree", ubicacionTreeWidget);
