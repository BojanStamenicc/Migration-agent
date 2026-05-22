<?php
namespace App\Services;

class HothServiceFinalizer {
    // When a HothServices order proves it will stay (>=30 days AND first payment received),
    // we copy it to the official orders table and delete it from hothservices_orders.
    // No order ever exists in both tables simultaneously.
    public function finalize($hsOrderId) {
        $hs = HothServicesOrder::find($hsOrderId);
        if (!$hs->isEligibleForConversion()) return;

        Order::create([
            'customer_id' => $hs->customer_id,
            'product_id'  => $hs->product_id,
            'type'        => 'converted',
            'created_at'  => $hs->created_at,
        ]);
        DB::delete("DELETE FROM hothservices_orders WHERE id = ?", [$hsOrderId]);
    }
}
