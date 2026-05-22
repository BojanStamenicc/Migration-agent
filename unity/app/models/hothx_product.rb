class HothxProduct < ApplicationRecord
  # Premium HothX product line. Legacy orders with product_id in 5000-5999 land here.
  # subscription_status: 'provisional' when sourced from legacy hothservices_orders,
  #                      'active' when sourced from legacy orders.
  belongs_to :customer
  has_many :subscription_orders

  validates :product_code, presence: true
  validates :subscription_status, inclusion: { in: %w[provisional active cancelled] }
  validates :original_source_table, inclusion: { in: %w[hothservices official] }
end
