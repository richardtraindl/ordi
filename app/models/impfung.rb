# == Schema Information
#
# Table name: impfungen
#
#  behandlung_id   :integer         not null
#  impfungswert_id :integer         not null
#  created_at      :datetime        not null
#  updated_at      :datetime        not null
#

class Impfung < ActiveRecord::Base
	self.table_name = "impfungen"
	
	has_many :behandlungen
	has_many :impfungswerte
	
	
	def self.impfungswerte_for_behandlung(behandlung_id)
		Impfung.select( 'impfungswert_id' ).where( 'impfungen.behandlung_id = ?', behandlung_id ).all().map { |rec| rec.impfungswert_id } 
	end
end
