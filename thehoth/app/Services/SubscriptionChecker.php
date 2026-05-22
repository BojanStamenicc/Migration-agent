<?php
namespace App\Services;

class SubscriptionChecker {
    // Determines whether an order is a campaign/subscription order.
    public function isSubscription($order) {
        // Primary rule: linked subscription with active-ish status
        if ($order->subscription_id !== null) {
            $sub = Subscription::find($order->subscription_id);
            if (in_array($sub->status, ['active', 'trialing', 'past_due'])) {
                return true;
            }
        }
        // Legacy pre-2023 fallback
        if ($order->has_recurring_items == 1) {
            return true;
        }
        return false;
    }

    public function classifyHothX($order) {
        // HothX product range 5000-5999. Some are always campaign, some never.
        if ($order->product_id >= 5000 && $order->product_id <= 5499) {
            return 'always_campaign'; // premium tier always subscription
        }
        if ($order->product_id >= 5500 && $order->product_id <= 5799) {
            return 'sometimes_campaign'; // depends on subscription_id + has_recurring_items
        }
        if ($order->product_id >= 5800 && $order->product_id <= 5999) {
            return 'never_campaign'; // one-time HothX add-ons
        }
        return 'not_hothx';
    }
}
