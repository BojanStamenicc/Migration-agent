<?php
namespace App\Services;

class OrderService {
    public function getOrderWithCampaign($orderId) {
        // Implicit join across orders + campaign_order (no FK in schema)
        $sql = "SELECT * FROM campaigns c
                JOIN campaign_order co ON c.id = co.campaign_id
                WHERE co.order_id = ?";
        return DB::select($sql, [$orderId]);
    }

    public function getOrderNotes($orderId) {
        // order_notes has no FK but uses order_id column
        return DB::select("SELECT * FROM order_notes WHERE order_id = ?", [$orderId]);
    }
}
